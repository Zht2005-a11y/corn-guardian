"""诊断历史存储层 —— 每次大屏识别落盘，可回看。

设计要点（对齐 session_store.py 的风格：零第三方依赖，仅标准库）：

- 存储：SQLite 单文件 ``<system_root>/history/diagnosis_history.db``；
  缩略图（原图 / Grad-CAM 叠加图）以 JPEG base64 直接存库，单库便于统计。
- 写入：``save_record()`` 只存缩略图（最长边 480px / JPEG q72），
  全尺寸原图不落库——回看场景够用，且避免库无限膨胀。
- 读取：
  - ``list_records()`` 列表（含 160px 小缩略图）+ 全局统计（今日次数/总数/病害分布），
    供大屏「历史记录」弹窗与个人中心「今日诊断」真实计数使用；
  - ``get_record()`` 单条详情（含热力图与飞防参数）。
- 清理：``delete_record()`` 单条删除；库表带 id 自增。

本模块零业务依赖（仅标准库），可独立导入测试。
"""
from __future__ import annotations

import base64
import io
import json
import logging
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image

logger = logging.getLogger("corn_system.history_store")

_SYSTEM_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = _SYSTEM_ROOT / "history" / "diagnosis_history.db"

_lock = threading.Lock()

_SCHEMA = """
CREATE TABLE IF NOT EXISTS diagnosis_history (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at    TEXT    NOT NULL,             -- ISO 本地时间
    class_en      TEXT    NOT NULL,             -- Blight / Common_Rust / ...
    class_name    TEXT    NOT NULL,             -- 中文病名（ Healthy=健康 ）
    confidence    REAL    NOT NULL,             -- 0-100
    severity      TEXT    NOT NULL,             -- 轻度/中度/重度/健康
    damage_rate   REAL    NOT NULL,             -- 受损叶面积比率 %
    model_used    TEXT    NOT NULL,
    inference_ms  REAL,
    prescription  TEXT,
    drone_params  TEXT,                         -- JSON：机型/亩喷施量/航高...
    boxes         TEXT,                         -- JSON：病斑 bbox
    thumb         TEXT,                         -- 原图缩略 JPEG base64（480px）
    heatmap       TEXT                          -- Grad-CAM 叠加缩略 JPEG base64
);
CREATE INDEX IF NOT EXISTS idx_hist_created ON diagnosis_history (created_at DESC);
"""

# 列表页用的小缩略图边长 / 详情页用的大缩略图边长（最长边，px）
_LIST_THUMB = 160
_FULL_THUMB = 480


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(_SCHEMA)
    conn.commit()


def _to_jpeg_b64(data: bytes, max_side: int) -> Optional[str]:
    """把图片字节缩放为 JPEG base64（data-url 前缀），失败返回 None。"""
    try:
        img = Image.open(io.BytesIO(data))
        img = img.convert("RGB")
        img.thumbnail((max_side, max_side), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=72)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception as e:  # noqa: BLE001
        logger.warning("history thumbnail encode failed: %s", e)
        return None


def _b64_to_jpeg_b64(b64: str, max_side: int) -> Optional[str]:
    """把（可能带 data-url 前缀的）base64 图片重编码为限定尺寸 JPEG base64。"""
    if not b64:
        return None
    try:
        raw = b64.split(",")[-1]
        return _to_jpeg_b64(base64.b64decode(raw), max_side)
    except Exception:  # noqa: BLE001
        return None


def save_record(
    *,
    image_bytes: bytes,
    gradcam_b64: str = "",
    class_en: str,
    class_name: str,
    confidence: float,
    severity: str,
    damage_rate: float,
    model_used: str = "",
    inference_ms: Optional[float] = None,
    prescription: str = "",
    drone_params: Optional[Dict[str, Any]] = None,
    boxes: Optional[List[Dict[str, Any]]] = None,
) -> Optional[int]:
    """保存一条诊断记录，返回记录 id；任何异常都不应影响主流程（返回 None）。"""
    try:
        thumb = _to_jpeg_b64(image_bytes, _FULL_THUMB)
        heatmap = _b64_to_jpeg_b64(gradcam_b64, _FULL_THUMB)
        with _lock, _conn() as conn:
            _ensure_schema(conn)
            cur = conn.execute(
                "INSERT INTO diagnosis_history"
                " (created_at, class_en, class_name, confidence, severity, damage_rate,"
                "  model_used, inference_ms, prescription, drone_params, boxes,"
                "  thumb, heatmap)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    datetime.now().isoformat(timespec="seconds"),
                    class_en, class_name, confidence, severity, damage_rate,
                    model_used, inference_ms, prescription,
                    json.dumps(drone_params or {}, ensure_ascii=False),
                    json.dumps(boxes or [], ensure_ascii=False),
                    thumb, heatmap,
                ),
            )
            return int(cur.lastrowid)
    except Exception as e:  # noqa: BLE001
        logger.warning("save_record failed (ignored): %s", e)
        return None


def list_records(limit: int = 50, offset: int = 0) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """按时间倒序返回记录列表（缩略图压缩到 160px）与统计信息。"""
    with _lock, _conn() as conn:
        _ensure_schema(conn)
        rows = conn.execute(
            "SELECT id, created_at, class_en, class_name, confidence, severity,"
            "       damage_rate, model_used, inference_ms, thumb"
            " FROM diagnosis_history ORDER BY id DESC LIMIT ? OFFSET ?",
            (max(1, min(limit, 200)), max(0, offset)),
        ).fetchall()

        today = datetime.now().strftime("%Y-%m-%d")
        total = conn.execute("SELECT COUNT(*) FROM diagnosis_history").fetchone()[0]
        today_cnt = conn.execute(
            "SELECT COUNT(*) FROM diagnosis_history WHERE created_at LIKE ?", (today + "%",)
        ).fetchone()[0]
        by_class = {
            r["class_en"]: {"name": r["class_name"], "count": r["c"]}
            for r in conn.execute(
                "SELECT class_en, MAX(class_name) AS class_name, COUNT(*) AS c"
                " FROM diagnosis_history GROUP BY class_en"
            ).fetchall()
        }

    items = []
    for r in rows:
        d = dict(r)
        d["thumb_small"] = _b64_to_jpeg_b64(d.pop("thumb") or "", _LIST_THUMB)
        items.append(d)

    stats = {"total": total, "today": today_cnt, "byClass": by_class}
    return items, stats


def count_today_by_class(class_en: str) -> int:
    """统计今天某个病害类别已诊断的次数（用于扩散风险告警）。"""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        with _lock, _conn() as conn:
            _ensure_schema(conn)
            return int(
                conn.execute(
                    "SELECT COUNT(*) FROM diagnosis_history WHERE class_en = ? AND created_at LIKE ?",
                    (class_en, today + "%"),
                ).fetchone()[0]
            )
    except Exception as e:  # noqa: BLE001
        logger.warning("count_today_by_class failed: %s", e)
        return 0


def get_record(rid: int) -> Optional[Dict[str, Any]]:
    """单条详情：含热力图、飞防参数 JSON。"""
    with _lock, _conn() as conn:
        _ensure_schema(conn)
        row = conn.execute(
            "SELECT * FROM diagnosis_history WHERE id = ?", (rid,)
        ).fetchone()
    if row is None:
        return None
    d = dict(row)
    for k in ("drone_params", "boxes"):
        try:
            d[k] = json.loads(d.get(k) or "null")
        except Exception:  # noqa: BLE001
            d[k] = None
    d["droneParams"] = d.pop("drone_params")
    return d


def delete_record(rid: int) -> bool:
    with _lock, _conn() as conn:
        _ensure_schema(conn)
        cur = conn.execute("DELETE FROM diagnosis_history WHERE id = ?", (rid,))
        return cur.rowcount > 0
