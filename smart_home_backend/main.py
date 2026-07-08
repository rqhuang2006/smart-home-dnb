from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from config import API_PREFIX, FRONTEND_DIR, PROJECT_ROOT, ensure_directories
from database.db import init_db
from routes import dashboard, devices, face, iot, persons, vision
from services.yolo_service import import_original_weight_if_missing
from utils.api_response import ApiError, error, ok


app = FastAPI(title="Smart Home Integrated Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(persons.router, prefix=API_PREFIX)
app.include_router(face.router, prefix=API_PREFIX)
app.include_router(vision.router, prefix=API_PREFIX)
app.include_router(devices.router, prefix=API_PREFIX)
app.include_router(iot.router, prefix=API_PREFIX)
app.include_router(dashboard.router, prefix=API_PREFIX)

app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")


@app.on_event("startup")
def startup() -> None:
    ensure_directories()
    init_db()
    import_original_weight_if_missing(
        PROJECT_ROOT
        / "incoming_modules"
        / "yolo_module"
        / "smart-home-dnb-yolo"
        / "smart_home_yolo_pack"
        / "weights"
        / "best.pt"
    )


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=error(exc.code, exc.message, exc.data))


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=400, content=error(4000, "request parameter error", None))


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = 4001 if exc.status_code == 404 else 4000
    message = str(exc.detail) if exc.detail else "request parameter error"
    return JSONResponse(status_code=exc.status_code, content=error(code, message, None))


@app.exception_handler(Exception)
async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content=error(5000, "backend internal error", None))


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health")
def health():
    return ok({"status": "running"})


@app.get(f"{API_PREFIX}/health")
def api_health():
    return ok({"status": "running"})
