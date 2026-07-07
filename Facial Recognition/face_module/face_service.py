from __future__ import annotations

import shutil
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

import numpy as np
from fastapi import UploadFile

from database.init_db import get_connection
from face_module.api_response import ApiError
from face_module.config import (
    ACCESS_IMAGES_DIR,
    EMBEDDINGS_DIR,
    FACES_DIR,
    MAX_UPLOAD_SIZE_MB,
    ensure_directories,
)
from face_module.face_utils import FaceEncoder, NoFaceFoundError, compare_embeddings


encoder = FaceEncoder()
TZ_SHANGHAI = timezone(timedelta(hours=8))


def now_iso() -> str:
    return datetime.now(TZ_SHANGHAI).replace(microsecond=0).isoformat()


def safe_filename(filename: str | None, fallback_ext: str = ".jpg") -> str:
    suffix = Path(filename or "").suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}:
        suffix = fallback_ext
    return f"{uuid.uuid4().hex}{suffix}"


async def save_upload_file(upload: UploadFile, target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    content = await upload.read()
    max_bytes = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if not content:
        raise ApiError(4000, "face_image is required")
    if len(content) > max_bytes:
        raise ApiError(4000, f"image is too large, max {MAX_UPLOAD_SIZE_MB} MB")
    path = target_dir / safe_filename(upload.filename)
    path.write_bytes(content)
    return path


def confidence_from_similarity(similarity: Optional[float]) -> float:
    if similarity is None:
        return 0.0
    return round(float(np.clip(similarity, 0.0, 1.0)), 4)


async def register_person(
    name: str,
    role: Optional[str],
    authorized: bool,
    face_image: UploadFile,
) -> dict[str, Any]:
    ensure_directories()
    clean_name = (name or "").strip()
    clean_role = (role or "student").strip() or "student"
    if not clean_name:
        raise ApiError(4000, "name is required")

    temp_dir = FACES_DIR / "_incoming"
    image_path = await save_upload_file(face_image, temp_dir)
    try:
        embedding_result = encoder.extract_embedding(image_path)
    except NoFaceFoundError as exc:
        image_path.unlink(missing_ok=True)
        raise ApiError(4002, "no face detected") from exc
    except Exception as exc:
        image_path.unlink(missing_ok=True)
        raise ApiError(4000, str(exc)) from exc

    embedding_tmp_path = EMBEDDINGS_DIR / f"{uuid.uuid4().hex}.npy"
    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)
    np.save(embedding_tmp_path, embedding_result.embedding)

    created_at = now_iso()
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO persons (
                    name, role, authorized, face_image_path,
                    face_embedding_path, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    clean_name,
                    clean_role,
                    1 if authorized else 0,
                    str(image_path),
                    str(embedding_tmp_path),
                    created_at,
                ),
            )
            person_id = int(cursor.lastrowid)

            person_dir = FACES_DIR / str(person_id)
            person_dir.mkdir(parents=True, exist_ok=True)
            final_image_path = person_dir / image_path.name
            final_embedding_path = EMBEDDINGS_DIR / f"person_{person_id}.npy"
            shutil.move(str(image_path), str(final_image_path))
            shutil.move(str(embedding_tmp_path), str(final_embedding_path))

            conn.execute(
                """
                UPDATE persons
                SET face_image_path = ?, face_embedding_path = ?
                WHERE id = ?
                """,
                (str(final_image_path), str(final_embedding_path), person_id),
            )
            conn.commit()
    except Exception:
        image_path.unlink(missing_ok=True)
        embedding_tmp_path.unlink(missing_ok=True)
        raise

    return {
        "person_id": person_id,
        "name": clean_name,
        "authorized": bool(authorized),
    }


def list_persons(authorized: Optional[bool] = None) -> list[dict[str, Any]]:
    sql = "SELECT id, name, role, authorized, created_at FROM persons"
    params: list[Any] = []
    if authorized is not None:
        sql += " WHERE authorized = ?"
        params.append(1 if authorized else 0)
    sql += " ORDER BY created_at DESC, id DESC"

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()

    return [
        {
            "person_id": int(row["id"]),
            "name": row["name"],
            "role": row["role"],
            "authorized": bool(row["authorized"]),
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def delete_person(person_id: int) -> dict[str, Any]:
    if person_id <= 0:
        raise ApiError(4000, "invalid person_id")

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, name, face_image_path, face_embedding_path
            FROM persons
            WHERE id = ?
            """,
            (person_id,),
        ).fetchone()
        if row is None:
            raise ApiError(4001, "person not found", None, status_code=404)

        conn.execute("DELETE FROM persons WHERE id = ?", (person_id,))
        conn.commit()

    image_path = Path(row["face_image_path"])
    embedding_path = Path(row["face_embedding_path"])
    image_path.unlink(missing_ok=True)
    embedding_path.unlink(missing_ok=True)

    person_dir = FACES_DIR / str(person_id)
    try:
        person_dir.rmdir()
    except OSError:
        pass

    return {
        "person_id": int(row["id"]),
        "name": row["name"],
        "deleted": True,
    }


async def verify_face(face_image: UploadFile) -> tuple[int, str, dict[str, Any]]:
    ensure_directories()
    target_dir = ACCESS_IMAGES_DIR / datetime.now(TZ_SHANGHAI).strftime("%Y-%m-%d")
    input_path = await save_upload_file(face_image, target_dir)

    try:
        probe = encoder.extract_embedding(input_path)
    except NoFaceFoundError:
        data = {
            "matched": False,
            "person_id": None,
            "name": None,
            "confidence": 0,
            "door_allowed": False,
            "reason": "no face detected",
        }
        write_access_log(
            person_id=None,
            matched=False,
            confidence=0,
            door_allowed=False,
            reason="no face detected",
            image_path=input_path,
        )
        return 4002, "no face detected", data

    best_person_id: Optional[int] = None
    best_name: Optional[str] = None
    best_distance: Optional[float] = None
    best_confidence = 0.0

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, name, face_embedding_path
            FROM persons
            WHERE authorized = 1
            ORDER BY id ASC
            """
        ).fetchall()

    for row in rows:
        embedding_path = Path(row["face_embedding_path"])
        if not embedding_path.exists():
            continue
        stored_embedding = np.load(embedding_path)
        distance, similarity = compare_embeddings(
            probe.embedding,
            stored_embedding,
            backend=encoder.backend,
        )
        confidence = confidence_from_similarity(similarity)
        if best_distance is None or distance < best_distance:
            best_distance = distance
            best_confidence = confidence
            best_person_id = int(row["id"])
            best_name = row["name"]

    matched = best_distance is not None and best_distance <= encoder.threshold
    if matched:
        data = {
            "matched": True,
            "person_id": best_person_id,
            "name": best_name,
            "confidence": best_confidence,
            "door_allowed": True,
            "reason": "authorized person",
        }
    else:
        data = {
            "matched": False,
            "person_id": None,
            "name": None,
            "confidence": best_confidence,
            "door_allowed": False,
            "reason": "unknown or unauthorized person",
        }

    write_access_log(
        person_id=data["person_id"],
        matched=data["matched"],
        confidence=data["confidence"],
        door_allowed=data["door_allowed"],
        reason=data["reason"],
        image_path=input_path,
    )
    return 0, "ok", data


def write_access_log(
    person_id: Optional[int],
    matched: bool,
    confidence: float,
    door_allowed: bool,
    reason: str,
    image_path: Path,
) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO access_logs (
                person_id, matched, confidence, door_allowed,
                reason, image_path, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                person_id,
                1 if matched else 0,
                float(confidence),
                1 if door_allowed else 0,
                reason,
                str(image_path),
                now_iso(),
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)


def query_logs(limit: int = 50) -> list[dict[str, Any]]:
    limit = max(1, min(limit, 500))
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT access_logs.*, persons.name AS person_name
            FROM access_logs
            LEFT JOIN persons ON access_logs.person_id = persons.id
            ORDER BY access_logs.created_at DESC, access_logs.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [_log_row_to_dict(row) for row in rows]


def latest_face_access() -> Optional[dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT access_logs.*, persons.name AS person_name
            FROM access_logs
            LEFT JOIN persons ON access_logs.person_id = persons.id
            ORDER BY access_logs.created_at DESC, access_logs.id DESC
            LIMIT 1
            """
        ).fetchone()
    if row is None:
        return None
    return {
        "matched": bool(row["matched"]),
        "name": row["person_name"],
        "door_allowed": bool(row["door_allowed"]),
        "created_at": row["created_at"],
    }


def _log_row_to_dict(row: Any) -> dict[str, Any]:
    return {
        "id": int(row["id"]),
        "person_id": int(row["person_id"]) if row["person_id"] is not None else None,
        "name": row["person_name"],
        "matched": bool(row["matched"]),
        "confidence": round(float(row["confidence"] or 0), 4),
        "door_allowed": bool(row["door_allowed"]),
        "reason": row["reason"],
        "image_path": row["image_path"],
        "created_at": row["created_at"],
    }

