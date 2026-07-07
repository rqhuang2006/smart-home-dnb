import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATABASE_DIR = BASE_DIR / "database"
DATA_DIR = BASE_DIR / "data"
IMAGES_DIR = DATA_DIR / "images"
STORAGE_DIR = BASE_DIR / "storage"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

DB_PATH = DATABASE_DIR / "smarthome.db"
FACES_DIR = IMAGES_DIR / "faces"
CAMERA_IMAGES_DIR = IMAGES_DIR / "camera"
ACCESS_IMAGES_DIR = IMAGES_DIR / "access"
EMBEDDINGS_DIR = DATA_DIR / "embeddings"

# Backwards-compatible name used by older code/tests.
AUTHORIZED_FACES_DIR = FACES_DIR

HARDWARE_MODE = os.getenv("HARDWARE_MODE", "mock").lower()
HARDWARE_DOOR_URL = os.getenv("HARDWARE_DOOR_URL", "http://127.0.0.1:9000/door/open")
DOOR_OPEN_DURATION_SECONDS = int(os.getenv("DOOR_OPEN_DURATION_SECONDS", "3"))

FACE_MATCH_THRESHOLD = float(os.getenv("FACE_MATCH_THRESHOLD", "0.55"))
OPENCV_MATCH_THRESHOLD = float(os.getenv("OPENCV_MATCH_THRESHOLD", "0.05"))
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "8"))


def ensure_directories() -> None:
    for path in [
        DATABASE_DIR,
        DATA_DIR,
        IMAGES_DIR,
        FACES_DIR,
        CAMERA_IMAGES_DIR,
        ACCESS_IMAGES_DIR,
        EMBEDDINGS_DIR,
        STATIC_DIR,
        TEMPLATES_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)

