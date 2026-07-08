from __future__ import annotations

from fastapi import APIRouter, File, Form, Query, UploadFile

from services import face_service
from utils.api_response import ok


router = APIRouter(tags=["persons"])


@router.post("/persons")
async def create_person(
    name: str = Form(...),
    role: str = Form("resident"),
    authorized: bool = Form(...),
    face_image: UploadFile = File(...),
):
    return ok(await face_service.register_person(name, role, authorized, face_image))


@router.get("/persons")
def get_persons(authorized: bool | None = Query(None)):
    return ok(face_service.list_persons(authorized=authorized))

@router.delete("/persons/{person_id}")
def delete_person(person_id: int):
    return ok(face_service.delete_person(person_id=person_id))
