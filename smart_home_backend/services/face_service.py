from __future__ import annotations

import shutil
import sys
import uuid
from pathlib import Path
from typing import Any

import numpy as np
from fastapi import UploadFile

from config import ACCESS_IMAGES_DIR, EMBEDDINGS_DIR, FACE_IMAGES_DIR, INCOMING_FACE_DIR, MAX_UPLOAD_SIZE_MB, ensure_directories
from database import db
from utils.api_response import ApiError


if str(INCOMING_FACE_DIR) not in sys.path:
    sys.path.insert(0, str(INCOMING_FACE_DIR))

from face_module.face_utils import FaceEncoder, NoFaceFoundError, compare_embeddings  # noqa: E402


encoder = FaceEncoder()


def _safe_filename(filename: str | None, fallback_ext: str = ".jpg") -> str:
    suffix = Path(filename or "").suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}:
        suffix = fallback_ext
    return f"{uuid.uuid4().hex}{suffix}"


async def _save_upload(upload: UploadFile, target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    content = await upload.read()
    if not content:
        raise ApiError(4000, "face_image is required")
    if len(content) > MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise ApiError(4000, f"image is too large, max {MAX_UPLOAD_SIZE_MB} MB")
    path = target_dir / _safe_filename(upload.filename)
    path.write_bytes(content)
    return path


def _confidence_from_similarity(similarity: float | None) -> float:
    if similarity is None:
        return 0.0
    return round(float(np.clip(similarity, 0.0, 1.0)), 4)


async def register_person(name: str, role: str | None, authorized: bool, face_image: UploadFile) -> dict[str, Any]:
    ensure_directories()
    clean_name = (name or "").strip()
    clean_role = (role or "resident").strip() or "resident"
    if not clean_name:
        raise ApiError(4000, "name is required")

    temp_path = await _save_upload(face_image, FACE_IMAGES_DIR / "_incoming")
    try:
        embedding_result = encoder.extract_embedding(temp_path)
    except NoFaceFoundError as exc:
        temp_path.unlink(missing_ok=True)
        raise ApiError(4002, "no face detected") from exc
    except Exception as exc:
        temp_path.unlink(missing_ok=True)
        raise ApiError(4000, str(exc)) from exc

    embedding_tmp = EMBEDDINGS_DIR / f"{uuid.uuid4().hex}.npy"
    np.save(embedding_tmp, embedding_result.embedding)
    created_at = db.now_iso()

    try:
        with db.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO persons(name, role, authorized, face_image_path, face_embedding_path, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (clean_name, clean_role, 1 if authorized else 0, str(temp_path), str(embedding_tmp), created_at),
            )
            person_id = int(cursor.lastrowid)
            person_dir = FACE_IMAGES_DIR / str(person_id)
            person_dir.mkdir(parents=True, exist_ok=True)
            final_image = person_dir / temp_path.name
            final_embedding = EMBEDDINGS_DIR / f"person_{person_id}.npy"
            shutil.move(str(temp_path), str(final_image))
            shutil.move(str(embedding_tmp), str(final_embedding))
            conn.execute(
                "UPDATE persons SET face_image_path = ?, face_embedding_path = ? WHERE id = ?",
                (str(final_image), str(final_embedding), person_id),
            )
            conn.commit()
    except Exception:
        temp_path.unlink(missing_ok=True)
        embedding_tmp.unlink(missing_ok=True)
        raise

    db.insert_image("face_register", str(final_image), "persons")
    return {
        "person_id": person_id,
        "name": clean_name,
        "role": clean_role,
        "authorized": bool(authorized),
        "created_at": created_at,
    }


def list_persons(authorized: bool | None = None) -> list[dict[str, Any]]:
    sql = "SELECT id, name, role, authorized, created_at FROM persons"
    params: list[Any] = []
    if authorized is not None:
        sql += " WHERE authorized = ?"
        params.append(1 if authorized else 0)
    sql += " ORDER BY created_at DESC, id DESC"
    with db.get_connection() as conn:
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

    with db.get_connection() as conn:
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

    person_dir = FACE_IMAGES_DIR / str(person_id)
    try:
        person_dir.rmdir()
    except OSError:
        pass

    return {
        "person_id": int(row["id"]),
        "name": row["name"],
        "deleted": True,
    }

async def verify_face(face_image: UploadFile) -> dict[str, Any]:
    ensure_directories()
    input_path = await _save_upload(face_image, ACCESS_IMAGES_DIR)
    db.insert_image("face_verify", str(input_path), "access")

    try:
        probe = encoder.extract_embedding(input_path)
    except NoFaceFoundError:
        data = {
            "matched": False,
            "person_id": None,
            "name": None,
            "confidence": 0.0,
            "door_allowed": False,
            "reason": "no face detected",
        }
        write_access_log(data, input_path)
        return data

    best_person_id: int | None = None
    best_name: str | None = None
    best_distance: float | None = None
    best_confidence = 0.0
    with db.get_connection() as conn:
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
        for probe_embedding in (probe.embedding, *probe.alternate_embeddings):
            distance, similarity = compare_embeddings(probe_embedding, stored_embedding, backend=encoder.backend)
            confidence = _confidence_from_similarity(similarity)
            if best_distance is None or distance < best_distance:
                best_distance = distance
                best_confidence = confidence
                best_person_id = int(row["id"])
                best_name = row["name"]

    matched = best_distance is not None and best_distance <= encoder.threshold
    data = {
        "matched": bool(matched),
        "person_id": best_person_id if matched else None,
        "name": best_name if matched else None,
        "confidence": best_confidence,
        "door_allowed": bool(matched),
        "reason": "authorized person" if matched else "unknown or unauthorized person",
    }
    write_access_log(data, input_path)
    return data


def write_access_log(result: dict[str, Any], image_path: Path) -> int:
    with db.get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO access_logs(person_id, matched, confidence, door_allowed, reason, image_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.get("person_id"),
                1 if result.get("matched") else 0,
                float(result.get("confidence") or 0),
                1 if result.get("door_allowed") else 0,
                str(result.get("reason") or ""),
                str(image_path),
                db.now_iso(),
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)


def latest_face_access() -> dict[str, Any] | None:
    with db.get_connection() as conn:
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
        "person_id": int(row["person_id"]) if row["person_id"] is not None else None,
        "name": row["person_name"],
        "confidence": round(float(row["confidence"] or 0), 4),
        "door_allowed": bool(row["door_allowed"]),
        "reason": row["reason"],
        "created_at": row["created_at"],
    }

