from fastapi import APIRouter, File, Query, UploadFile

from face_module.api_response import error, ok
from face_module.face_service import latest_face_access, query_logs, verify_face


router = APIRouter(prefix="/api/v1", tags=["face"])


@router.post("/face/verify")
async def api_verify_face(face_image: UploadFile = File(...)):
    code, message, data = await verify_face(face_image=face_image)
    if code == 0:
        return ok(data)
    return error(code, message, data)


@router.get("/access/logs")
def api_get_logs(limit: int = Query(50, ge=1, le=500)):
    return ok(query_logs(limit=limit))


@router.get("/dashboard/summary")
def api_dashboard_summary():
    return ok({"latest_face_access": latest_face_access()})
