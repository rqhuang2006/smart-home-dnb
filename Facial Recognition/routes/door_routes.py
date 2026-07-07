from pydantic import BaseModel, Field
from fastapi import APIRouter

from face_module.api_response import ApiError, ok
from face_module.door_control import control_door


router = APIRouter(prefix="/api/v1", tags=["door"])


class DoorControlRequest(BaseModel):
    action: str = Field(..., examples=["open"])
    reason: str = ""
    duration_seconds: int = Field(3, ge=1, le=60)


@router.post("/devices/door/control")
def api_control_door(payload: DoorControlRequest):
    try:
        result = control_door(
            action=payload.action,
            reason=payload.reason,
            duration_seconds=payload.duration_seconds,
        )
    except ValueError as exc:
        raise ApiError(4000, str(exc)) from exc
    except Exception as exc:
        raise ApiError(5001, "device offline or control failed") from exc

    return ok({"door_open": result["door_open"], "action": result["action"]})
