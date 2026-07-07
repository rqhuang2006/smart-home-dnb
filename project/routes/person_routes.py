from fastapi import APIRouter, File, Form, Query, UploadFile

from face_module.face_service import delete_person, list_persons, register_person
from face_module.api_response import ok


router = APIRouter(prefix="/api/v1", tags=["persons"])


@router.post("/persons")
async def api_register_person(
    name: str = Form(...),
    role: str = Form("student"),
    authorized: bool = Form(...),
    face_image: UploadFile = File(...),
):
    data = await register_person(
        name=name,
        role=role,
        authorized=authorized,
        face_image=face_image,
    )
    return ok(data)


@router.get("/persons")
def api_list_persons(authorized: bool | None = Query(None)):
    return ok(list_persons(authorized=authorized))


@router.delete("/persons/{person_id}")
def api_delete_person(person_id: int):
    return ok(delete_person(person_id=person_id))
