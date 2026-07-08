from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
API_PREFIX = "/api/v1"

DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "smart_home.db"

IMAGES_DIR = DATA_DIR / "images"
FACE_IMAGES_DIR = IMAGES_DIR / "faces"
ACCESS_IMAGES_DIR = IMAGES_DIR / "access"
CAMERA_IMAGES_DIR = IMAGES_DIR / "camera"
EMBEDDINGS_DIR = DATA_DIR / "embeddings"

MODELS_DIR = BASE_DIR / "models"
YOLO_MODEL_PATH = MODELS_DIR / "yolo" / "best.pt"

FRONTEND_DIR = BASE_DIR / "frontend"

INCOMING_FACE_DIR = PROJECT_ROOT / "incoming_modules" / "face_module" / "Facial Recognition"

MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "20"))
FACE_MATCH_THRESHOLD = float(os.getenv("FACE_MATCH_THRESHOLD", "0.55"))
FAN_AUTO_TEMPERATURE = float(os.getenv("FAN_AUTO_TEMPERATURE", "30.0"))
YOLO_CONFIDENCE = float(os.getenv("YOLO_CONFIDENCE", "0.35"))
YOLO_IMAGE_SIZE = int(os.getenv("YOLO_IMAGE_SIZE", "640"))
YOLO_DEVICE = os.getenv("YOLO_DEVICE", "cpu")


def ensure_directories() -> None:
    for path in [
        DATA_DIR,
        IMAGES_DIR,
        FACE_IMAGES_DIR,
        ACCESS_IMAGES_DIR,
        CAMERA_IMAGES_DIR,
        EMBEDDINGS_DIR,
        MODELS_DIR / "yolo",
        FRONTEND_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)
