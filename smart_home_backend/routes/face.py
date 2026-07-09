from __future__ import annotations

from fastapi import APIRouter, File, UploadFile

from services import face_service
from utils.api_response import ok


router = APIRouter(tags=["face"])


@router.post("/face/verify")
async def verify_face(face_image: UploadFile = File(...)):
    return ok(await face_service.verify_face(face_image))
