from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import DB_PATH, ensure_directories


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().replace(microsecond=0).isoformat()


def get_connection() -> sqlite3.Connection:
    ensure_directories()
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    ensure_directories()
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS persons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT,
                authorized INTEGER NOT NULL DEFAULT 1,
                face_image_path TEXT NOT NULL,
                face_embedding_path TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS access_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id INTEGER,
                matched INTEGER NOT NULL DEFAULT 0,
                confidence REAL NOT NULL DEFAULT 0,
                door_allowed INTEGER NOT NULL DEFAULT 0,
                reason TEXT NOT NULL,
                image_path TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_type TEXT NOT NULL,
                file_path TEXT NOT NULL,
                source TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS detection_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id INTEGER,
                image_path TEXT NOT NULL,
                objects_json TEXT NOT NULL,
                trigger_action TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS sensor_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                temperature REAL,
                light_brightness INTEGER,
                door_open INTEGER NOT NULL DEFAULT 0,
                window_open INTEGER NOT NULL DEFAULT 0,
                fan_on INTEGER NOT NULL DEFAULT 0,
                sensor_type TEXT NOT NULL DEFAULT 'telemetry',
                raw_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS device_commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device TEXT NOT NULL,
                action TEXT NOT NULL,
                payload_json TEXT NOT NULL DEFAULT '{}',
                result_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS device_status (
                device TEXT PRIMARY KEY,
                status_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_persons_authorized ON persons(authorized);
            CREATE INDEX IF NOT EXISTS idx_access_logs_created_at ON access_logs(created_at);
            CREATE INDEX IF NOT EXISTS idx_detection_created_at ON detection_records(created_at);
            CREATE INDEX IF NOT EXISTS idx_sensor_created_type ON sensor_records(created_at, sensor_type);
            CREATE INDEX IF NOT EXISTS idx_commands_created_device ON device_commands(created_at, device);
            """
        )
        _seed_device_status(conn)
        conn.commit()


def _seed_device_status(conn: sqlite3.Connection) -> None:
    defaults = {
        "light": {"on": False, "brightness": 0, "mode": "mock"},
        "fan": {"on": False, "mode": "mock"},
        "door": {"open": False, "mode": "mock"},
        "window": {"open": False, "mode": "mock"},
        "environment": {"temperature": None, "light_brightness": None},
    }
    timestamp = now_iso()
    for device, status in defaults.items():
        conn.execute(
            """
            INSERT OR IGNORE INTO device_status(device, status_json, updated_at)
            VALUES (?, ?, ?)
            """,
            (device, json.dumps(status, ensure_ascii=False), timestamp),
        )


def insert_image(image_type: str, file_path: str, source: str | None = None) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO images(image_type, file_path, source, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (image_type, file_path, source, now_iso()),
        )
        conn.commit()
        return int(cursor.lastrowid)


def get_image(image_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM images WHERE id = ?", (image_id,)).fetchone()
    return dict(row) if row else None


def insert_detection_record(
    image_id: int | None,
    image_path: str,
    objects: list[dict[str, Any]],
    trigger_action: dict[str, Any] | None,
) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO detection_records(image_id, image_path, objects_json, trigger_action, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                image_id,
                image_path,
                json.dumps(objects, ensure_ascii=False),
                json.dumps(trigger_action, ensure_ascii=False) if trigger_action else None,
                now_iso(),
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)


def list_detection_records(start: str | None = None, end: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    sql = "SELECT * FROM detection_records WHERE 1=1"
    params: list[Any] = []
    if start:
        sql += " AND created_at >= ?"
        params.append(start)
    if end:
        sql += " AND created_at <= ?"
        params.append(end)
    sql += " ORDER BY created_at DESC, id DESC LIMIT ?"
    params.append(max(1, min(limit, 200)))
    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_detection_row(row) for row in rows]


def latest_detection() -> dict[str, Any] | None:
    records = list_detection_records(limit=1)
    return records[0] if records else None


def _detection_row(row: sqlite3.Row) -> dict[str, Any]:
    objects = json.loads(row["objects_json"] or "[]")
    trigger_action = json.loads(row["trigger_action"]) if row["trigger_action"] else None
    return {
        "record_id": int(row["id"]),
        "image_id": int(row["image_id"]) if row["image_id"] is not None else None,
        "image_path": row["image_path"],
        "objects": objects,
        "trigger_action": trigger_action,
        "created_at": row["created_at"],
    }


def insert_sensor_record(payload: dict[str, Any], fan_on: bool) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO sensor_records(
                temperature, light_brightness, door_open, window_open, fan_on,
                sensor_type, raw_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.get("temperature"),
                payload.get("light_brightness"),
                1 if payload.get("door_open") else 0,
                1 if payload.get("window_open") else 0,
                1 if fan_on else 0,
                str(payload.get("type") or payload.get("sensor_type") or "telemetry"),
                json.dumps(payload, ensure_ascii=False),
                now_iso(),
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)


def list_sensor_records(
    start: str | None = None,
    end: str | None = None,
    sensor_type: str | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    sql = "SELECT * FROM sensor_records WHERE 1=1"
    params: list[Any] = []
    if start:
        sql += " AND created_at >= ?"
        params.append(start)
    if end:
        sql += " AND created_at <= ?"
        params.append(end)
    if sensor_type and sensor_type != "all":
        sql += " AND sensor_type = ?"
        params.append(sensor_type)
    sql += " ORDER BY created_at DESC, id DESC LIMIT ?"
    params.append(max(1, min(limit, 1000)))
    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [
        {
            "id": int(row["id"]),
            "temperature": row["temperature"],
            "light_brightness": row["light_brightness"],
            "door_open": bool(row["door_open"]),
            "window_open": bool(row["window_open"]),
            "fan_on": bool(row["fan_on"]),
            "type": row["sensor_type"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def set_device_status(device: str, status: dict[str, Any]) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO device_status(device, status_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(device) DO UPDATE SET
                status_json = excluded.status_json,
                updated_at = excluded.updated_at
            """,
            (device, json.dumps(status, ensure_ascii=False), now_iso()),
        )
        conn.commit()


def get_device_status_map() -> dict[str, dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM device_status").fetchall()
    return {
        row["device"]: {
            **json.loads(row["status_json"] or "{}"),
            "updated_at": row["updated_at"],
        }
        for row in rows
    }


def insert_device_command(device: str, action: str, payload: dict[str, Any], result: dict[str, Any]) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO device_commands(device, action, payload_json, result_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                device,
                action,
                json.dumps(payload, ensure_ascii=False),
                json.dumps(result, ensure_ascii=False),
                now_iso(),
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)
