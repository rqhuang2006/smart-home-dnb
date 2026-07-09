from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ApiError(Exception):
    code: int
    message: str
    data: Any = None
    status_code: int = 400


def ok(data: Any = None) -> dict[str, Any]:
    return {"code": 0, "message": "ok", "data": {} if data is None else data}


def error(code: int = 4001, message: str = "person not found", data: Any = None) -> dict[str, Any]:
    return {"code": code, "message": message, "data": data}
