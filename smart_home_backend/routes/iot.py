from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel

from database import db
from services import device_service
from utils.api_response import ok


router = APIRouter(tags=["iot"])


class TelemetryRequest(BaseModel):
    temperature: float | None = None
    light_brightness: int | None = None
    door_open: bool | None = None
    window_open: bool | None = None
    fan_on: bool | None = None
    type: str | None = "telemetry"


@router.post("/iot/telemetry")
def telemetry(payload: TelemetryRequest):
    if hasattr(payload, "model_dump"):
        data: dict[str, Any] = payload.model_dump(exclude_none=True)
    else:
        data = payload.dict(exclude_none=True)
    return ok(device_service.ingest_telemetry(data))


@router.get("/sensors/history")
def sensor_history(
    start: str | None = Query(None),
    end: str | None = Query(None),
    type: str | None = Query("all"),
    limit: int = Query(200, ge=1, le=1000),
):
    return ok(db.list_sensor_records(start=start, end=end, sensor_type=type, limit=limit))


