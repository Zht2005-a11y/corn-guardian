"""会话找回存储层 —— 移植 Claude Code 的 sessionStorage / --resume 机制。

每段问答对话是一个 append-only 的 JSONL 文件（等价 Claude Code 的
``~/.claude/projects/<project>/<session>.jsonl`` transcript）：

    <system_root>/sessions/<session_id>.jsonl

每行一个条目，形如（对齐 sessionStorage.ts 的 TranscriptMessage，本项目为线性链）::

    {"type": "user", "uuid": "...", "parentUuid": "...", "timestamp": "...",
     "sessionId": "s_xxx", "message": {"role": "user", "content": "..."}}

type 取值：
- ``user`` / ``assistant`` / ``tool_result``：transcript 消息行（参与上下文恢复）；
- ``isMeta`` 标记：``[stop_hook 反馈]``、截断续写指令等「注入型」用户消息——
  模型上下文有效，但不参与标题提取、不对外展示（对齐 Claude Code 的 isMeta 行）；
- system 消息**不写盘**：其中含日期/农时等逐轮变化的环境块，恢复时重建
  （等价 Claude Code resume 时对系统上下文的重新 stamping）。

与 Claude Code 源码的对应关系：
- 列表：``stat`` mtime 降序 + 头/尾各 64KB 轻读（sessionStorage.ts readLiteMetadata），
  不做全量解析；标题优先级 lastPrompt > firstPrompt（本项目不产生 custom-title 行）；
- 恢复：全量解析 → 过滤 meta/非 transcript 行 → OpenAI 格式 messages 列表
  （conversationRecovery.ts 的 deserializeMessagesWithInterruptDetection 线性简化版）；
- 写入：一轮问答结束后批量 append 本轮增量（recordTranscript + insertMessageChain 的
  简化——本系统无并行分支 DAG，parentUuid 即线性前一行的 uuid）。

本模块零业务依赖（仅标准库），可独立导入测试。
"""
from __future__ import annotations

import json
import logging
import os
import re
import uuid as uuid_lib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("corn_system.session_store")

# ── 存储布局 ────────────────────────────────────────────────────────────
# <system_root>/sessions/：等价 Claude Code 的 ~/.claude/projects/<project>/；
# 大屏后端是单一产品（非多项目 CLI），故不按 cwd 分项目目录，直接平铺。
SYSTEM_ROOT = Path(__file__).resolve().parent.parent
SESSIONS_DIR = SYSTEM_ROOT / "sessions"

# 轻量读取窗口（对齐 Claude Code LITE_READ_BUF_SIZE=65536）
LITE_READ_BYTES = 65536
# 列表标题截断长度（面板宽度有限，比 Claude Code 的 200 字符收紧）
TITLE_MAX_CHARS = 80

# 注入型 meta 用户消息前缀（与 llm_client 中实际注入的文案保持一致）：
# 模型上下文有效，但不应作为会话标题，也不在恢复展示中对外呈现
META_USER_PREFIXES = ("[stop_hook 反馈]", "输出被长度限制截断")

_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9_-]")


# ── 基础工具 ────────────────────────────────────────────────────────────
def _safe_name(session_id: str) -> str:
    """session_id 是前端传来的任意字符串，落盘前做白名单过滤（防路径穿越）。"""
    name = _SAFE_NAME_RE.sub("_", str(session_id or "").strip())
    return (name or "unnamed")[:80]


def _session_path(session_id: str) -> Path:
    return SESSIONS_DIR / f"{_safe_name(session_id)}.jsonl"


def _is_meta_user_message(msg: Dict[str, Any]) -> bool:
    """是否为注入型 meta 用户消息（stop_hook 反馈 / 截断续写指令）"""
    content = msg.get("content")
    return (
        msg.get("role") == "user"
        and isinstance(content, str)
        and content.startswith(META_USER_PREFIXES)
    )


def is_plain_user_message(msg: Dict[str, Any]) -> bool:
    """真实的用户提问（非 meta 注入、非空）——既用于标题提取，也用于截断边界判定。"""
    content = msg.get("content")
    return (
        msg.get("role") == "user"
        and isinstance(content, str)
        and content.strip()
        and not content.startswith(META_USER_PREFIXES)
    )


def session_exists(session_id: str) -> bool:
    return bool(session_id) and _session_path(session_id).exists()


# ── 写入（append-only）──────────────────────────────────────────────────
# 链尾 uuid 缓存：等价 Claude Code getSessionMessages 的已写 uuid 集合；
# 进程重启后缓存为空，从文件尾反读最后一行的 uuid 补齐。
_TAIL_UUID: Dict[str, str] = {}


def _last_complete_uuid(path: Path) -> Optional[str]:
    """读文件尾 8KB，取最后一条完整 JSONL 行的 uuid（崩溃时的半行会被跳过）。"""
    try:
        size = path.stat().st_size
        with open(path, "rb") as f:
            f.seek(max(0, size - 8192))
            data = f.read().decode("utf-8", "ignore")
    except OSError:
        return None
    for line in reversed(data.splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
            if isinstance(row, dict) and row.get("uuid"):
                return str(row["uuid"])
        except Exception:
            continue
    return None


def _append_rows(session_id: str, rows: List[tuple]) -> None:
    """把 (type, message, is_meta) 三元组追加进 transcript，parentUuid 线性串联。"""
    path = _session_path(session_id)
    key = _safe_name(session_id)

    parent = _TAIL_UUID.get(key)
    if parent is None and path.exists():
        parent = _last_complete_uuid(path)

    now = datetime.now().isoformat(timespec="seconds")
    lines = []
    for row_type, msg, is_meta in rows:
        entry: Dict[str, Any] = {
            "type": row_type,
            "uuid": str(uuid_lib.uuid4()),
            "parentUuid": parent,
            "sessionId": session_id,  # 原始 id（落盘名已 sanitize，这里保留原值）
            "timestamp": now,
            "message": msg,
        }
        if is_meta:
            entry["isMeta"] = True
        parent = entry["uuid"]
        lines.append(json.dumps(entry, ensure_ascii=False) + "\n")

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.writelines(lines)
    _TAIL_UUID[key] = parent


def record_turn(session_id: Optional[str], turn_messages: List[Dict[str, Any]], reply: str = "") -> None:
    """把一轮问答的增量消息追加进 transcript（等价 recordTranscript 的增量语义）。

    - ``turn_messages``：本轮新增的消息（调用方已排除 system 与恢复基底），
      含 user 提问、assistant 的 tool_calls 消息、tool 检索结果、stop_hook 注入消息等；
    - ``reply``：被打断时已流出的半截回答，作为一条 assistant 行补记
      （与 llm_client.save_session 的快照语义一致，保证磁盘与内存快照内容对齐）。
    写入失败只告警，绝不影响主问答流程。
    """
    if not session_id:
        return
    msgs = [dict(m) for m in turn_messages if m.get("role") != "system"]
    if reply and (not msgs or msgs[-1].get("role") != "assistant"):
        msgs.append({"role": "assistant", "content": reply})
    if not msgs:
        return

    rows = []
    for m in msgs:
        role = m.get("role")
        if role == "user":
            rows.append(("user", m, _is_meta_user_message(m)))
        elif role == "assistant":
            rows.append(("assistant", m, False))
        elif role == "tool":
            rows.append(("tool_result", m, False))
    try:
        _append_rows(session_id, rows)
    except Exception as exc:  # 磁盘写失败不阻断问答主流程
        logger.warning(f"会话 transcript 写入失败（session={session_id}）: {exc}")


def delete_session(session_id: str) -> bool:
    """删除会话（磁盘文件 + 链尾缓存）。返回是否删到了真实文件。"""
    if not session_id:
        return False
    path = _session_path(session_id)
    _TAIL_UUID.pop(_safe_name(session_id), None)
    if path.exists():
        path.unlink()
        return True
    return False


# ── 读取（全量解析，用于恢复）────────────────────────────────────────────
def read_rows(session_id: str) -> List[Dict[str, Any]]:
    """全量读取 transcript 行；损坏行（如崩溃时的半行）静默跳过。"""
    path = _session_path(session_id)
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
                if isinstance(row, dict):
                    rows.append(row)
            except Exception:
                continue
    return rows


_TRANSCRIPT_TYPES = ("user", "assistant", "tool_result")


def transcript_messages(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """transcript 行 → OpenAI 格式 messages 列表（等价 loadTranscriptFile + 线性链回溯）。

    注入型 meta 行（stop_hook 反馈 / 截断续写指令）保留——它们本身就是
    合法的模型上下文；system 消息不在盘上（由调用方每轮重建）。
    """
    msgs = []
    for row in rows:
        if row.get("type") in _TRANSCRIPT_TYPES:
            message = row.get("message")
            if isinstance(message, dict):
                msgs.append(message)
    return msgs


def transcript_meta(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """计算列表/详情展示元信息：首条提问（标题候选）与中断检测。

    中断语义对齐 Claude Code conversationRecovery 的 interrupted 判定：
    - 最后一条是 tool_result（检索完成但回答没生成完）→ 可「继续」补全；
    - 最后一条是 user 提问且无回答 → 上一轮被打断在回答前；
    - 最后一条 assistant 有正文 → 会话正常结束。
    """
    msgs = transcript_messages(rows)
    first_prompt = ""
    for m in msgs:
        if is_plain_user_message(m):
            first_prompt = str(m["content"])[:TITLE_MAX_CHARS]
            break

    interrupted: Optional[str] = None
    for m in reversed(msgs):
        role = m.get("role")
        if role == "tool":
            interrupted = "tool_result_pending"
            break
        if role == "assistant":
            content = (m.get("content") or "").strip()
            if content:
                interrupted = None
            elif m.get("tool_calls"):
                interrupted = "tool_pending"
            else:
                interrupted = "half_answer"
            break
        if role == "user":
            interrupted = "meta_pending" if _is_meta_user_message(m) else "unanswered_prompt"
            break

    return {
        "first_prompt": first_prompt,
        "interrupted": interrupted,
        "message_count": len(msgs),
    }


def transcript_display(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """transcript 行 → 前端气泡数据（{role: 'user'|'ai', text, ts, searchQuery?}）。

    - meta 注入消息不外显；tool 结果行不单独外显，而是把检索词挂到
      紧随其后的 assistant 气泡上（与实时流里「🔍 已联网检索」标签对齐）；
    - 半截 assistant（content 为空但带 tool_calls）跳过，等待后续行补齐。
    """
    out: List[Dict[str, Any]] = []
    pending_query: Optional[str] = None
    for row in rows:
        row_type = row.get("type")
        msg = row.get("message") or {}
        if row_type == "user" and not row.get("isMeta") and is_plain_user_message(msg):
            out.append({"role": "user", "text": msg["content"], "ts": row.get("timestamp")})
        elif row_type == "assistant":
            for tc in msg.get("tool_calls") or []:
                try:
                    args = json.loads((tc.get("function") or {}).get("arguments") or "{}")
                except Exception:
                    args = {}
                q = args.get("query")
                if q:
                    pending_query = q
            content = msg.get("content")
            if content and content.strip():
                item: Dict[str, Any] = {"role": "ai", "text": content, "ts": row.get("timestamp")}
                if pending_query:
                    item["searchQuery"] = pending_query
                    pending_query = None
                out.append(item)
        # tool_result 行不产生气泡（检索词已通过 pending_query 体现）
    return out


# ── 列表（stat + 头尾轻读，对齐 getSessionFilesLite / readLiteMetadata）──
def _read_text_window(path: Path, tail: bool = False) -> str:
    """读文件头或尾各 LITE_READ_BYTES 的文本窗口（轻量元信息抓取用）。"""
    total = path.stat().st_size
    n = min(LITE_READ_BYTES, total)
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        if tail:
            f.seek(max(0, total - n))
        return f.read(n)


def _parse_window_lines(window: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for line in window.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
            if isinstance(row, dict):
                rows.append(row)
        except Exception:
            continue  # 窗口边界可能切断半行，跳过即可
    return rows


def _fmt_time(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


def _lite_interrupted(tail_rows: List[Dict[str, Any]]) -> bool:
    """用尾部窗口做轻量中断检测：最后一条 transcript 行是否未收尾。"""
    for row in reversed(tail_rows):
        row_type = row.get("type")
        if row_type not in _TRANSCRIPT_TYPES:
            continue
        msg = row.get("message") or {}
        if row_type == "tool_result":
            return True
        if row_type == "assistant":
            return not (msg.get("content") or "").strip()
        if row_type == "user":
            return bool(row.get("isMeta")) or not is_plain_user_message(msg)
    return False


def list_sessions(limit: int = 50) -> List[Dict[str, Any]]:
    """历史会话列表（--resume 选择器数据源）：mtime 降序 + 头尾 64KB 轻读标题。

    标题优先级 lastPrompt > firstPrompt（对齐 Claude Code readLiteMetadata 的
    customTitle > aiTitle > lastPrompt > summary > firstPrompt，本项目只产生后两级）。
    """
    if not SESSIONS_DIR.is_dir():
        return []
    entries = []
    for entry in os.scandir(SESSIONS_DIR):
        if not (entry.is_file() and entry.name.endswith(".jsonl")):
            continue
        try:
            st = entry.stat()
        except OSError:
            continue
        entries.append((st.st_mtime, st.st_ctime, entry.path, st.st_size))
    entries.sort(key=lambda t: t[0], reverse=True)

    sessions: List[Dict[str, Any]] = []
    for mtime, ctime, path, size in entries[: max(1, limit)]:
        head_rows = _parse_window_lines(_read_text_window(Path(path)))
        tail_rows = _parse_window_lines(_read_text_window(Path(path), tail=True))
        first_prompt = ""
        for row in head_rows:
            if row.get("type") == "user" and not row.get("isMeta") and is_plain_user_message(row.get("message") or {}):
                first_prompt = str((row["message"])["content"])[:TITLE_MAX_CHARS]
                break
        last_prompt = ""
        for row in reversed(tail_rows):
            if row.get("type") == "user" and not row.get("isMeta") and is_plain_user_message(row.get("message") or {}):
                last_prompt = str(row["message"]["content"])[:TITLE_MAX_CHARS]
                break
        sessions.append({
            "session_id": Path(path).name[: -len(".jsonl")],
            # 标题用「最近一次提问」最便于辨认（Claude Code lastPrompt 同语义）；空会话兜底
            "title": last_prompt or first_prompt or "(session)",
            "first_prompt": first_prompt,
            "last_prompt": last_prompt,
            "modified": _fmt_time(mtime),
            "created": _fmt_time(ctime),
            "size_bytes": size,
            "interrupted": _lite_interrupted(tail_rows),
        })
    return sessions
