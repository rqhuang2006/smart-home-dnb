from __future__ import annotations

from typing import Any

from config import FAN_AUTO_TEMPERATURE
from database import db


def flatten_status() -> dict[str, Any]:
    status = db.get_device_status_map()
    light = status.get("light", {})
    fan = status.get("fan", {})
    door = status.get("door", {})
    window = status.get("window", {})
    environment = status.get("environment", {})
    return {
        "light_on": bool(light.get("on")),
        "light_brightness": int(light.get("brightness") or 0),
        "fan_on": bool(fan.get("on")),
        "door_open": bool(door.get("open")),
        "window_open": bool(window.get("open")),
        "temperature": environment.get("temperature"),
        "mode": "mock",
        "raw": status,
    }


def control_light(on: bool, brightness: int = 80, source: str = "api") -> dict[str, Any]:
    brightness = max(0, min(100, int(brightness if on else 0)))
    status = {"on": bool(on), "brightness": brightness, "mode": "mock", "source": source}
    db.set_device_status("light", status)
    result = {"device": "light", "light_on": bool(on), "brightness": brightness, "mode": "mock"}
    command_id = db.insert_device_command("light", "on" if on else "off", status, result)
    return {**result, "command_id": command_id}


def control_fan(on: bool, source: str = "api", temperature: float | None = None) -> dict[str, Any]:
    status = {"on": bool(on), "mode": "mock", "source": source, "temperature": temperature}
    db.set_device_status("fan", status)
    result = {"device": "fan", "fan_on": bool(on), "mode": "mock"}
    command_id = db.insert_device_command("fan", "on" if on else "off", status, result)
    return {**result, "command_id": command_id}


def control_door(action: str, reason: str = "", duration_seconds: int = 3) -> dict[str, Any]:
    normalized = (action or "").lower().strip()
    if normalized not in {"open", "close"}:
        raise ValueError("action must be 'open' or 'close'")
    status = {
        "open": normalized == "open",
        "mode": "mock",
        "reason": reason,
        "duration_seconds": duration_seconds if normalized == "open" else 0,
    }
    db.set_device_status("door", status)
    result = {"door_open": status["open"], "action": normalized, "mode": "mock"}
    command_id = db.insert_device_command("door", normalized, status, result)
    return {**result, "command_id": command_id}


def ingest_telemetry(payload: dict[str, Any]) -> dict[str, Any]:
    temperature = payload.get("temperature")
    auto_fan = temperature is not None and float(temperature) > FAN_AUTO_TEMPERATURE
    requested_fan = payload.get("fan_on")
    fan_on = bool(auto_fan or requested_fan)

    environment = {
        "temperature": temperature,
        "light_brightness": payload.get("light_brightness"),
        "mode": "mock",
    }
    db.set_device_status("environment", environment)
    if payload.get("light_brightness") is not None:
        light_on = int(payload.get("light_brightness") or 0) > 0
        db.set_device_status("light", {"on": light_on, "brightness": int(payload.get("light_brightness") or 0), "mode": "mock"})
    if payload.get("door_open") is not None:
        db.set_device_status("door", {"open": bool(payload.get("door_open")), "mode": "mock"})
    if payload.get("window_open") is not None:
        db.set_device_status("window", {"open": bool(payload.get("window_open")), "mode": "mock"})
    if fan_on:
        db.set_device_status("fan", {"on": True, "mode": "mock", "source": "auto_temperature" if auto_fan else "telemetry"})

    record_id = db.insert_sensor_record(payload, fan_on=fan_on)
    return {
        "record_id": record_id,
        "fan_on": fan_on,
        "auto_fan_on": bool(auto_fan),
        "device_status": flatten_status(),
    }
