from __future__ import annotations

from fastapi import APIRouter, File, Form, Query, UploadFile

from database import db
from services import yolo_service
from utils.api_response import ApiError, ok


router = APIRouter(tags=["vision"])


@router.post("/images")
async def upload_image(image: UploadFile = File(...), source: str = Form("camera")):
    return ok(await yolo_service.save_camera_image(image, source=source))


@router.post("/vision/detect")
async def detect(
    image: UploadFile | None = File(None),
    image_id: int | None = Form(None),
    source: str = Form("upload"),
):
    if image is not None:
        return ok(await yolo_service.detect_upload(image, source=source))
    if image_id is not None:
        return ok(yolo_service.detect_saved_image(image_id))
    raise ApiError(4000, "image or image_id is required")


@router.get("/vision/records")
def records(
    start: str | None = Query(None),
    end: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    return ok(db.list_detection_records(start=start, end=end, limit=limit))
