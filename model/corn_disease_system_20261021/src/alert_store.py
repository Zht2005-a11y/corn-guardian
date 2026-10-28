"""告警存储层 —— 由诊断结果自动生成，替代大屏里写死的「3 条告警」。

设计要点（与 history_store / session_store 一致：零第三方依赖，仅标准库）：

- 存储：SQLite 单文件 ``<system_root>/history/alerts.db``
  （与诊断历史同目录，便于一起备份；两库分表，互不影响）。
- 生成：诊断结束后调用 ``emit_for_diagnosis()``，按规则写入，
  同一规则对同一条诊断记录只写一次（按 ref_id + rule 去重）。
- 规则（当前）：
  · rule=critical_lesion  受损率 ≥30% 的非健康叶片      → urgent
  · rule=low_confidence   置信度 <75%                   → warning
  · rule=spread_risk      同一种病害当日第 3/5/10 次    → warning
  · rule=no_lesion        健康叶片                       → 不产生告警
- 读取：``list_alerts()`` 返回列表 + 统计（未读/总数/今日），供顶部胶囊与弹窗使用。
"""
from __future__ import annotations

import logging
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("corn_system.alert_store")

_SYSTEM_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = _SYSTEM_ROOT / "history" / "alerts.db"

_lock = threading.Lock()

_SCHEMA = """
CREATE TABLE IF NOT EXISTS alerts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT    NOT NULL,
    level      TEXT    NOT NULL,   -- urgent | warning | info
    rule       TEXT    NOT NULL,   -- 触发规则，用于去重
    title      TEXT    NOT NULL,
    detail     TEXT,
    source     TEXT,               -- diagnosis | env | system
    ref_id     INTEGER,            -- 关联 diagnosis_history.id
    is_read    INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_read ON alerts (is_read);
CREATE UNIQUE INDEX IF NOT EXISTS idx_alerts_dedup ON alerts (rule, ref_id);
"""

# 同病害当日重复出现时，在这些次数上各报一次，避免刷屏
_SPREAD_THRESHOLDS = (3, 5, 10)


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(_SCHEMA)
    conn.commit()


def _insert(conn: sqlite3.Connection, **kw: Any) -> Optional[int]:
    """按 (rule, ref_id) 去重插入，返回新 id；重复或失败返回 None。"""
    try:
        cur = conn.execute(
            "INSERT OR IGNORE INTO alerts"
            " (created_at, level, rule, title, detail, source, ref_id)"
            " VALUES (?,?,?,?,?,?,?)",
            (
                datetime.now().isoformat(timespec="seconds"),
                kw["level"], kw["rule"], kw["title"],
                kw.get("detail", ""), kw.get("source", "diagnosis"), kw.get("ref_id"),
            ),
        )
        return int(cur.lastrowid) if cur.rowcount else None
    except Exception as e:  # noqa: BLE001
        logger.warning("insert alert failed: %s", e)
        return None


def _exists_today(conn: sqlite3.Connection, rule: str) -> bool:
    """同一条规则今天是否已经报过（按天去重，避免每条诊断刷一条同样的告警）。"""
    today = datetime.now().strftime("%Y-%m-%d")
    row = conn.execute(
        "SELECT 1 FROM alerts WHERE rule = ? AND created_at LIKE ? LIMIT 1",
        (rule, today + "%"),
    ).fetchone()
    return row is not None


def emit_for_diagnosis(
    *,
    record_id: Optional[int],
    class_en: str,
    class_cn: str,
    severity: str,
    damage_rate: float,
    confidence: float,
    filename: str = "",
    same_class_today: int = 0,
) -> List[Dict[str, Any]]:
    """根据一次诊断结果生成告警（去重）。返回本次新建的告警列表。"""
    created: List[Dict[str, Any]] = []
    if not record_id:
        return created

    try:
        with _lock, _conn() as conn:
            _ensure_schema(conn)

            # 1) 重病斑：受损率 ≥30%（同一病害每天只报一次，避免每条诊断都刷一条）
            if class_en != "Healthy" and damage_rate >= 30:
                rule = f"critical_lesion:{class_en}"
                if not _exists_today(conn, rule):
                    a = {
                        "level": "urgent",
                        "rule": rule,
                        "title": f"{class_cn} 受损率 {damage_rate}%，已达{severity.split(' ')[0]}级",
                        "detail": f"样本 {filename or '未命名'} 检出大面积病斑，建议立即组织飞防并复查周边地块。",
                        "ref_id": record_id,
                    }
                    if _insert(conn, **a):
                        created.append({**a, "created_at": datetime.now().isoformat(timespec="seconds")})

            # 2) 低置信度：需人工复核（每天只报一次）
            if confidence < 75:
                rule = "low_confidence"
                if not _exists_today(conn, rule):
                    a = {
                        "level": "warning",
                        "rule": rule,
                        "title": f"识别置信度偏低 {confidence}%，需人工复核",
                        "detail": f"样本 {filename or '未命名'} 的结论不稳定，建议补拍或换角度重拍后再施药。",
                        "ref_id": record_id,
                    }
                    if _insert(conn, **a):
                        created.append({**a, "created_at": datetime.now().isoformat(timespec="seconds")})

            # 3) 扩散风险：同一病害当日累计到 3/5/10 次、之后每 5 次各报一次
            if class_en != "Healthy":
                cnt = int(same_class_today or 0)
                if cnt in _SPREAD_THRESHOLDS or (cnt >= 10 and cnt % 5 == 0):
                    rule = f"spread_risk:{class_en}:{cnt}"
                    a = {
                        "level": "warning",
                        "rule": rule,
                        "title": f"{class_cn} 今日已检出 {cnt} 次，存在扩散风险",
                        "detail": "同一病害短时间内重复出现，建议扩大到周边地块巡查并及时施药。",
                        "ref_id": record_id,
                    }
                    if _insert(conn, **a):
                        created.append({**a, "created_at": datetime.now().isoformat(timespec="seconds")})
    except Exception as e:  # noqa: BLE001
        logger.warning("emit_for_diagnosis failed (ignored): %s", e)

    return created


def list_alerts(limit: int = 50, unread_only: bool = False) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """告警列表（时间倒序）+ 统计（未读/总数/今日）。"""
    with _lock, _conn() as conn:
        _ensure_schema(conn)
        sql = "SELECT * FROM alerts"
        if unread_only:
            sql += " WHERE is_read = 0"
        sql += " ORDER BY id DESC LIMIT ?"
        rows = conn.execute(sql, (max(1, min(limit, 200)),)).fetchall()

        total = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
        unread = conn.execute("SELECT COUNT(*) FROM alerts WHERE is_read = 0").fetchone()[0]
        today = datetime.now().strftime("%Y-%m-%d")
        today_cnt = conn.execute(
            "SELECT COUNT(*) FROM alerts WHERE created_at LIKE ?", (today + "%",)
        ).fetchone()[0]

    items = []
    for r in rows:
        d = dict(r)
        d["isRead"] = bool(d.pop("is_read"))
        items.append(d)
    return items, {"unread": unread, "total": total, "today": today_cnt}


def mark_read(alert_id: int) -> bool:
    with _lock, _conn() as conn:
        _ensure_schema(conn)
        cur = conn.execute("UPDATE alerts SET is_read = 1 WHERE id = ?", (alert_id,))
        return cur.rowcount > 0


def mark_all_read() -> int:
    with _lock, _conn() as conn:
        _ensure_schema(conn)
        cur = conn.execute("UPDATE alerts SET is_read = 1 WHERE is_read = 0")
        return cur.rowcount or 0


def delete_alert(alert_id: int) -> bool:
    with _lock, _conn() as conn:
        _ensure_schema(conn)
        cur = conn.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))
        return cur.rowcount > 0
