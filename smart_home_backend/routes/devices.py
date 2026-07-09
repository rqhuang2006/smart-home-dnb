from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter

from services import device_service
from utils.api_response import ApiError, ok


router = APIRouter(tags=["devices"])


class DoorControlRequest(BaseModel):
    action: str = Field(..., examples=["open"])
    reason: str = ""
    duration_seconds: int = Field(3, ge=1, le=60)


class LightControlRequest(BaseModel):
    on: bool
    brightness: int = Field(80, ge=0, le=100)
    source: str = "api"


class FanControlRequest(BaseModel):
    on: bool
    source: str = "api"
    temperature: float | None = None


@router.get("/devices/status")
def device_status():
    return ok(device_service.flatten_status())


@router.post("/devices/door/control")
def door_control(payload: DoorControlRequest):
    try:
        return ok(device_service.control_door(payload.action, payload.reason, payload.duration_seconds))
    except ValueError as exc:
        raise ApiError(4000, str(exc)) from exc


@router.post("/devices/light/control")
def light_control(payload: LightControlRequest):
    return ok(device_service.control_light(payload.on, payload.brightness, payload.source))


@router.post("/devices/fan/control")
def fan_control(payload: FanControlRequest):
    return ok(device_service.control_fan(payload.on, payload.source, payload.temperature))
