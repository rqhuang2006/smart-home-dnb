from datetime import datetime, timezone, timedelta
from typing import Any, Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


API_PREFIX = "/api/v1"
CHINA_TZ = timezone(timedelta(hours=8))
AUTO_FAN_THRESHOLD = 30.0


app = FastAPI(
    title="Smart Home Backend API",
    description="Mock backend API for the DnB smart home project.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def now_iso() -> str:
    return datetime.now(CHINA_TZ).isoformat(timespec="seconds")


def ok(data: Any) -> dict[str, Any]:
    return {"code": 0, "message": "ok", "data": data}


class FaceVerifyRequest(BaseModel):
    name: str | None = Field(default=None, description="Mock name. Use 张三/李四 for authorized users.")
    confidence: float | None = Field(default=None, ge=0, le=1)


class DetectRequest(BaseModel):
    image_id: int | None = None
    image_path: str = "/data/images/camera/mock.jpg"


class ImageCreateRequest(BaseModel):
    image_path: str = "/data/images/camera/mock.jpg"
    source: Literal["camera", "manual", "upload", "mock"] = "mock"


class LightControlRequest(BaseModel):
    on: bool = True
    brightness: int = Field(default=80, ge=0, le=100)
    source: str = "gui"


class FanControlRequest(BaseModel):
    on: bool = True
    source: Literal["gui", "auto_temperature", "mock"] = "gui"
    temperature: float | None = None


class TelemetryRequest(BaseModel):
    temperature: float = 29.5
    light_brightness: int = Field(default=80, ge=0, le=100)
    door_open: bool = False
    window_open: bool = True
    fan_on: bool = False


class DoorControlRequest(BaseModel):
    action: Literal["open", "close"] = "open"
    reason: str = "manual"
    duration_seconds: int | None = Field(default=3, ge=0, le=30)


device_status = {
    "temperature": 29.5,
    "fan_on": True,
    "light_on": True,
    "light_brightness": 80,
    "door_open": False,
    "window_open": True,
    "updated_at": now_iso(),
}


sensor_history = [
    {
        "record_id": 1,
        "temperature": 26.8,
        "light_brightness": 40,
        "door_open": False,
        "window_open": False,
        "fan_on": False,
        "created_at": "2026-07-06T09:00:00+08:00",
    },
    {
        "record_id": 2,
        "temperature": 29.5,
        "light_brightness": 80,
        "door_open": False,
        "window_open": True,
        "fan_on": True,
        "created_at": "2026-07-06T21:30:00+08:00",
    },
]


authorized_people = {
    "张三": {"person_id": 1, "name": "张三", "confidence": 0.92},
    "李四": {"person_id": 2, "name": "李四", "confidence": 0.89},
}

latest_face_access: dict[str, Any] = {}
latest_detection: dict[str, Any] = {}
detection_records: list[dict[str, Any]] = [
    {
        "record_id": 1,
        "image_id": 201,
        "image_path": "/data/images/camera/sample_20260708_120000.jpg",
        "objects": [
            {"label": "person", "confidence": 0.87, "bbox": [120, 80, 260, 360]},
            {"label": "light_bulb", "confidence": 0.76, "bbox": [300, 100, 380, 190]},
        ],
        "trigger_action": {
            "type": "light_on",
            "executed": True,
            "reason": "detected light_bulb",
        },
        "created_at": "2026-07-08T12:00:00+08:00",
    }
]


@app.get(f"{API_PREFIX}/health")
def health() -> dict[str, Any]:
    return ok(
        {
            "service": "smart-home-backend",
            "status": "running",
            "mode": "mock",
            "device": "Orange Pi ready",
            "time": now_iso(),
        }
    )


@app.get(f"{API_PREFIX}/devices/status")
def get_device_status() -> dict[str, Any]:
    return ok(device_status)


@app.get(f"{API_PREFIX}/sensors/history")
def get_sensor_history(
    start: str | None = None,
    end: str | None = None,
    type: Literal["all", "temperature", "light", "door", "window"] = "all",
) -> dict[str, Any]:
    # Mock mode keeps filtering intentionally light. D can later replace this with DB queries.
    records = sensor_history
    if type == "temperature":
        records = [{"record_id": r["record_id"], "temperature": r["temperature"], "created_at": r["created_at"]} for r in records]
    elif type == "light":
        records = [{"record_id": r["record_id"], "light_brightness": r["light_brightness"], "created_at": r["created_at"]} for r in records]
    elif type == "door":
        records = [{"record_id": r["record_id"], "door_open": r["door_open"], "created_at": r["created_at"]} for r in records]
    elif type == "window":
        records = [{"record_id": r["record_id"], "window_open": r["window_open"], "created_at": r["created_at"]} for r in records]

    return ok(records)


@app.post(f"{API_PREFIX}/iot/telemetry")
def create_telemetry(payload: TelemetryRequest) -> dict[str, Any]:
    record_id = sensor_history[-1]["record_id"] + 1 if sensor_history else 1
    fan_on = payload.fan_on or payload.temperature >= AUTO_FAN_THRESHOLD
    record = {
        "record_id": record_id,
        "temperature": payload.temperature,
        "light_brightness": payload.light_brightness,
        "door_open": payload.door_open,
        "window_open": payload.window_open,
        "fan_on": fan_on,
        "auto_fan_triggered": payload.temperature >= AUTO_FAN_THRESHOLD,
        "created_at": now_iso(),
    }
    sensor_history.append(record)
    device_status.update(
        {
            "temperature": payload.temperature,
            "light_brightness": payload.light_brightness,
            "light_on": payload.light_brightness > 0,
            "door_open": payload.door_open,
            "window_open": payload.window_open,
            "fan_on": fan_on,
            "updated_at": record["created_at"],
        }
    )
    return ok({"record_id": record_id, "saved": True, "record": record})


@app.post(f"{API_PREFIX}/images")
def create_image_record(payload: ImageCreateRequest) -> dict[str, Any]:
    return ok(
        {
            "image_id": len(detection_records) + 200,
            "image_path": payload.image_path,
            "source": payload.source,
            "created_at": now_iso(),
        }
    )


@app.post(f"{API_PREFIX}/face/verify")
def verify_face(payload: FaceVerifyRequest) -> dict[str, Any]:
    person = authorized_people.get(payload.name or "")
    matched = person is not None
    confidence = payload.confidence if payload.confidence is not None else (person["confidence"] if person else 0.31)

    if matched and confidence >= 0.75:
        result = {
            "matched": True,
            "person_id": person["person_id"],
            "name": person["name"],
            "confidence": confidence,
            "door_allowed": True,
            "reason": "authorized person",
        }
    else:
        result = {
            "matched": False,
            "person_id": None,
            "name": payload.name,
            "confidence": confidence,
            "door_allowed": False,
            "reason": "unknown or unauthorized person",
        }

    device_status["door_open"] = result["door_allowed"]
    device_status["updated_at"] = now_iso()
    latest_face_access.clear()
    latest_face_access.update({**result, "created_at": device_status["updated_at"]})
    return ok(result)


@app.post(f"{API_PREFIX}/vision/detect")
def detect_objects(payload: DetectRequest) -> dict[str, Any]:
    objects = [
        {"label": "person", "confidence": 0.87, "bbox": [120, 80, 260, 360]},
        {"label": "light_bulb", "confidence": 0.76, "bbox": [300, 100, 380, 190]},
    ]
    device_status["light_on"] = True
    device_status["light_brightness"] = max(device_status["light_brightness"], 80)
    device_status["updated_at"] = now_iso()

    detection_result = {
        "record_id": detection_records[-1]["record_id"] + 1 if detection_records else 1,
        "image_id": payload.image_id,
        "image_path": payload.image_path,
        "objects": objects,
        "trigger_action": {
            "type": "light_on",
            "executed": True,
            "reason": "detected light_bulb",
        },
        "created_at": now_iso(),
    }
    detection_records.append(detection_result)
    latest_detection.clear()
    latest_detection.update(detection_result)
    return ok(detection_result)


@app.get(f"{API_PREFIX}/vision/records")
def get_vision_records(start: str | None = None, end: str | None = None) -> dict[str, Any]:
    return ok(detection_records)


@app.post(f"{API_PREFIX}/devices/light/control")
def control_light(payload: LightControlRequest) -> dict[str, Any]:
    device_status["light_on"] = payload.on
    device_status["light_brightness"] = payload.brightness if payload.on else 0
    device_status["updated_at"] = now_iso()
    return ok(
        {
            "light_on": device_status["light_on"],
            "light_brightness": device_status["light_brightness"],
            "source": payload.source,
        }
    )


@app.post(f"{API_PREFIX}/devices/fan/control")
def control_fan(payload: FanControlRequest) -> dict[str, Any]:
    device_status["fan_on"] = payload.on
    if payload.temperature is not None:
        device_status["temperature"] = payload.temperature
    device_status["updated_at"] = now_iso()
    return ok(
        {
            "fan_on": device_status["fan_on"],
            "temperature": device_status["temperature"],
            "source": payload.source,
        }
    )


@app.post(f"{API_PREFIX}/devices/door/control")
def control_door(payload: DoorControlRequest) -> dict[str, Any]:
    device_status["door_open"] = payload.action == "open"
    device_status["updated_at"] = now_iso()
    return ok(
        {
            "door_open": device_status["door_open"],
            "action": payload.action,
            "reason": payload.reason,
            "duration_seconds": payload.duration_seconds,
        }
    )


@app.get(f"{API_PREFIX}/dashboard/summary")
def dashboard_summary() -> dict[str, Any]:
    return ok(
        {
            "device_status": device_status,
            "latest_face_access": latest_face_access or None,
            "latest_detection": latest_detection or None,
        }
    )
