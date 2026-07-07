from __future__ import annotations

from typing import Any, Dict

import requests

from face_module.config import (
    DOOR_OPEN_DURATION_SECONDS,
    HARDWARE_DOOR_URL,
    HARDWARE_MODE,
)

_door_open = False


def control_door(action: str, reason: str = "", duration_seconds: int | None = None) -> Dict[str, Any]:
    global _door_open

    normalized_action = (action or "").lower().strip()
    duration = duration_seconds or DOOR_OPEN_DURATION_SECONDS
    if normalized_action not in {"open", "close"}:
        raise ValueError("action must be 'open' or 'close'")

    if HARDWARE_MODE == "mock":
        _door_open = normalized_action == "open"
        return {
            "door_open": _door_open,
            "action": normalized_action,
            "mode": "mock",
            "reason": reason,
            "duration_seconds": duration if normalized_action == "open" else 0,
        }

    if HARDWARE_MODE == "http":
        response = requests.post(
            HARDWARE_DOOR_URL,
            json={
                "action": normalized_action,
                "reason": reason,
                "duration_seconds": duration,
            },
            timeout=3,
        )
        response.raise_for_status()
        _door_open = normalized_action == "open"
        return {
            "door_open": _door_open,
            "action": normalized_action,
            "mode": "http",
            "hardware_response": response.text[:200],
        }

    raise RuntimeError("Set HARDWARE_MODE to mock or http")


# Backwards-compatible helpers for old imports.
def mock_open_door() -> str:
    control_door("open", "legacy mock open", DOOR_OPEN_DURATION_SECONDS)
    return "MOCK_SUCCESS"


def open_door() -> Dict[str, str]:
    result = control_door("open", "legacy open", DOOR_OPEN_DURATION_SECONDS)
    return {
        "status": "MOCK_SUCCESS" if result["mode"] == "mock" else "HTTP_SUCCESS",
        "mode": str(result["mode"]),
        "detail": "Door opened.",
    }
