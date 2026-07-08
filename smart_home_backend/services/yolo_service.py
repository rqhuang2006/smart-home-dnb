from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from threading import Lock
from typing import Any

from fastapi import UploadFile

from config import CAMERA_IMAGES_DIR, MAX_UPLOAD_SIZE_MB, YOLO_CONFIDENCE, YOLO_DEVICE, YOLO_IMAGE_SIZE, YOLO_MODEL_PATH, ensure_directories
from database import db
from utils.api_response import ApiError

try:
    from ultralytics import YOLO
except Exception as exc:
    YOLO = None
    YOLO_IMPORT_ERROR = exc
else:
    YOLO_IMPORT_ERROR = None


_model: Any = None
_model_lock = Lock()


def _safe_filename(filename: str | None, fallback_ext: str = ".jpg") -> str:
    suffix = Path(filename or "").suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}:
        suffix = fallback_ext
    return f"{uuid.uuid4().hex}{suffix}"


async def save_camera_image(upload: UploadFile, source: str = "upload") -> dict[str, Any]:
    ensure_directories()
    content = await upload.read()
    if not content:
        raise ApiError(4000, "image is required")
    if len(content) > MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise ApiError(4000, f"image is too large, max {MAX_UPLOAD_SIZE_MB} MB")
    path = CAMERA_IMAGES_DIR / _safe_filename(upload.filename)
    path.write_bytes(content)
    image_id = db.insert_image("camera", str(path), source)
    return {"image_id": image_id, "image_path": str(path), "source": source}


def get_model() -> Any:
    global _model
    if _model is not None:
        return _model
    if YOLO is None:
        raise ApiError(5001, f"ultralytics import failed: {YOLO_IMPORT_ERROR}", None, status_code=500)
    if not YOLO_MODEL_PATH.exists():
        raise ApiError(5001, f"YOLO model not found: {YOLO_MODEL_PATH}", None, status_code=500)
    with _model_lock:
        if _model is None:
            _model = YOLO(str(YOLO_MODEL_PATH))
    return _model


def detect_image_path(image_path: str | Path, image_id: int | None = None) -> dict[str, Any]:
    ensure_directories()
    path = Path(image_path)
    if not path.exists():
        raise ApiError(4001, "image not found", None, status_code=404)

    model = get_model()
    results = model.predict(
        source=str(path),
        conf=YOLO_CONFIDENCE,
        imgsz=YOLO_IMAGE_SIZE,
        device=YOLO_DEVICE,
        save=False,
        verbose=False,
    )
    result = results[0]
    names = result.names
    objects: list[dict[str, Any]] = []

    if result.boxes is not None:
        for box in result.boxes:
            cls_id = int(box.cls[0])
            confidence = float(box.conf[0])
            xyxy = [float(v) for v in box.xyxy[0].tolist()]
            label = str(names.get(cls_id, cls_id))
            objects.append(
                {
                    "label": label,
                    "confidence": round(confidence, 4),
                    "bbox": {
                        "x1": round(xyxy[0], 2),
                        "y1": round(xyxy[1], 2),
                        "x2": round(xyxy[2], 2),
                        "y2": round(xyxy[3], 2),
                    },
                }
            )

    trigger_action = _trigger_action(objects)
    record_id = db.insert_detection_record(image_id, str(path), objects, trigger_action)
    return {
        "record_id": record_id,
        "image_id": image_id,
        "image_path": str(path),
        "objects": objects,
        "trigger_action": trigger_action,
        "created_at": db.now_iso(),
    }


async def detect_upload(upload: UploadFile, source: str = "upload") -> dict[str, Any]:
    image = await save_camera_image(upload, source=source)
    return detect_image_path(image["image_path"], image_id=image["image_id"])


def detect_saved_image(image_id: int) -> dict[str, Any]:
    image = db.get_image(image_id)
    if image is None:
        raise ApiError(4001, "image not found", None, status_code=404)
    return detect_image_path(image["file_path"], image_id=image_id)


def _trigger_action(objects: list[dict[str, Any]]) -> dict[str, Any] | None:
    target_labels = {"drone", "fire_extinguisher"}
    matched = []
    for obj in objects:
        label = str(obj.get("label", "")).strip().lower().replace("-", "_").replace(" ", "_")
        if label in target_labels:
            matched.append(obj)
    if not matched:
        return None
    return {
        "type": "vision_alert",
        "action": "notify",
        "reason": "target object detected",
        "targets": matched,
    }


def import_original_weight_if_missing(source_path: Path) -> None:
    if YOLO_MODEL_PATH.exists() or not source_path.exists():
        return
    YOLO_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, YOLO_MODEL_PATH)

