from __future__ import annotations

from fastapi import APIRouter

from database import db
from services import device_service, face_service
from utils.api_response import ok


router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/summary")
def dashboard_summary():
    return ok(
        {
            "device_status": device_service.flatten_status(),
            "latest_face_access": face_service.latest_face_access(),
            "latest_detection": db.latest_detection(),
        }
    )
