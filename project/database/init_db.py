import sqlite3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from face_module.config import DB_PATH, ensure_directories


REQUIRED_ACCESS_LOG_COLUMNS = {
    "id",
    "person_id",
    "matched",
    "confidence",
    "door_allowed",
    "reason",
    "image_path",
    "created_at",
}


def get_connection() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    return {row["name"] for row in conn.execute(f"PRAGMA table_info({table_name})")}


def _move_legacy_access_logs(conn: sqlite3.Connection) -> None:
    if not _table_exists(conn, "access_logs"):
        return
    columns = _columns(conn, "access_logs")
    if REQUIRED_ACCESS_LOG_COLUMNS.issubset(columns):
        return

    suffix = 1
    while _table_exists(conn, f"access_logs_legacy_{suffix}"):
        suffix += 1
    conn.execute(f"ALTER TABLE access_logs RENAME TO access_logs_legacy_{suffix}")


def init_db() -> None:
    ensure_directories()
    with get_connection() as conn:
        _move_legacy_access_logs(conn)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS persons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT,
                authorized INTEGER NOT NULL DEFAULT 1,
                face_image_path TEXT NOT NULL,
                face_embedding_path TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
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
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_persons_authorized ON persons(authorized)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_access_logs_created_at ON access_logs(created_at)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_access_logs_person_id ON access_logs(person_id)"
        )
        conn.commit()


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
