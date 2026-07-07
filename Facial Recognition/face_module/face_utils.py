from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from face_module.config import FACE_MATCH_THRESHOLD, OPENCV_MATCH_THRESHOLD

try:
    import face_recognition  # type: ignore
except Exception:
    face_recognition = None


class NoFaceFoundError(ValueError):
    pass


@dataclass
class FaceEmbeddingResult:
    embedding: np.ndarray
    backend: str
    face_count: int
    threshold: float


class FaceEncoder:
    def __init__(self) -> None:
        self.backend = "face_recognition" if face_recognition is not None else "opencv"
        self.threshold = (
            FACE_MATCH_THRESHOLD if self.backend == "face_recognition" else OPENCV_MATCH_THRESHOLD
        )

    def extract_embedding(self, image_path: str | Path) -> FaceEmbeddingResult:
        path = str(image_path)
        if self.backend == "face_recognition":
            return self._extract_with_face_recognition(path)
        return self._extract_with_opencv(path)

    def _extract_with_face_recognition(self, image_path: str) -> FaceEmbeddingResult:
        image = face_recognition.load_image_file(image_path)
        locations = face_recognition.face_locations(image, model="hog")
        if not locations:
            raise NoFaceFoundError("No face detected in the uploaded image.")

        encodings = face_recognition.face_encodings(image, known_face_locations=locations)
        if not encodings:
            raise NoFaceFoundError("Face detected, but embedding extraction failed.")

        embedding = np.asarray(encodings[0], dtype=np.float32)
        return FaceEmbeddingResult(
            embedding=embedding,
            backend="face_recognition",
            face_count=len(locations),
            threshold=self.threshold,
        )

    def _extract_with_opencv(self, image_path: str) -> FaceEmbeddingResult:
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("Uploaded file is not a readable image.")

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
        detector = cv2.CascadeClassifier(str(cascade_path))
        faces = detector.detectMultiScale(
            gray,
            scaleFactor=1.08,
            minNeighbors=5,
            minSize=(60, 60),
        )
        if len(faces) == 0:
            raise NoFaceFoundError("No face detected in the uploaded image.")

        x, y, w, h = sorted(faces, key=lambda item: item[2] * item[3], reverse=True)[0]
        face = gray[y : y + h, x : x + w]
        face = cv2.resize(face, (96, 96), interpolation=cv2.INTER_AREA)
        face = cv2.equalizeHist(face)

        dct = cv2.dct(np.float32(face) / 255.0)[:24, :24].flatten()
        hist = cv2.calcHist([face], [0], None, [32], [0, 256]).flatten()
        hist = hist / max(float(hist.sum()), 1.0)
        small = cv2.resize(face, (16, 16), interpolation=cv2.INTER_AREA).flatten() / 255.0

        embedding = np.concatenate([dct, hist, small]).astype(np.float32)
        embedding = normalize_embedding(embedding)
        return FaceEmbeddingResult(
            embedding=embedding,
            backend="opencv",
            face_count=len(faces),
            threshold=self.threshold,
        )


def normalize_embedding(embedding: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(embedding))
    if norm == 0:
        return embedding.astype(np.float32)
    return (embedding / norm).astype(np.float32)


def average_embeddings(embeddings: list[np.ndarray]) -> np.ndarray:
    if not embeddings:
        raise ValueError("At least one valid face image is required.")
    mean_embedding = np.mean(np.stack(embeddings), axis=0)
    return normalize_embedding(mean_embedding)


def compare_embeddings(
    probe_embedding: np.ndarray,
    stored_embedding: np.ndarray,
    backend: Optional[str] = None,
) -> tuple[float, float]:
    if backend == "opencv":
        probe = normalize_embedding(probe_embedding)
        stored = normalize_embedding(stored_embedding)
        similarity = float(np.clip(np.dot(probe, stored), -1.0, 1.0))
        distance = 1.0 - similarity
        return distance, similarity

    distance = float(np.linalg.norm(probe_embedding - stored_embedding))
    similarity = float(max(0.0, 1.0 - distance))
    return distance, similarity

