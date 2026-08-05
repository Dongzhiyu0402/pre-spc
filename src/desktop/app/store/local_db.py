"""本地 SQLite 缓存：查重历史 + 设置 + 会话。

离线模式（AC-16 桌面端条款：原文不出本机，仅存指纹/结果）。
"""

import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path

from app.config import DB_PATH, LOCAL_DATA_DIR

_LOCK = threading.Lock()


def _connect() -> sqlite3.Connection:
    LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _LOCK, _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS check_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                plan_code TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'succeeded',
                created_at TEXT NOT NULL,
                result_json TEXT NOT NULL DEFAULT '{}',
                synced INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.commit()


def insert_check_record(file_name: str, plan_code: str, result: dict) -> int:
    with _LOCK, _connect() as conn:
        cur = conn.execute(
            "INSERT INTO check_records (file_name, plan_code, status, created_at, result_json) VALUES (?, ?, 'succeeded', ?, ?)",
            (file_name, plan_code, datetime.now().isoformat(timespec="seconds"), json.dumps(result, ensure_ascii=False)),
        )
        conn.commit()
        return int(cur.lastrowid)


def list_check_records(limit: int = 50) -> list[dict]:
    with _LOCK, _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM check_records ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    records = []
    for row in rows:
        item = dict(row)
        try:
            item["result"] = json.loads(item.pop("result_json"))
        except json.JSONDecodeError:
            item["result"] = {}
        records.append(item)
    return records


def get_check_record(record_id: int) -> dict | None:
    with _LOCK, _connect() as conn:
        row = conn.execute("SELECT * FROM check_records WHERE id = ?", (record_id,)).fetchone()
    if row is None:
        return None
    item = dict(row)
    try:
        item["result"] = json.loads(item.pop("result_json"))
    except json.JSONDecodeError:
        item["result"] = {}
    return item


def list_unsynced_records() -> list[dict]:
    with _LOCK, _connect() as conn:
        rows = conn.execute("SELECT * FROM check_records WHERE synced = 0").fetchall()
    return [dict(r) for r in rows]


def mark_synced(record_id: int) -> None:
    with _LOCK, _connect() as conn:
        conn.execute("UPDATE check_records SET synced = 1 WHERE id = ?", (record_id,))
        conn.commit()


def delete_record(record_id: int) -> None:
    with _LOCK, _connect() as conn:
        conn.execute("DELETE FROM check_records WHERE id = ?", (record_id,))
        conn.commit()
