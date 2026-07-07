from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from database.init_db import init_db
from face_module.api_response import ApiError, error
from face_module.config import STATIC_DIR, TEMPLATES_DIR, ensure_directories
from routes.door_routes import router as door_router
from routes.face_routes import router as face_router
from routes.person_routes import router as person_router


app = FastAPI(
    title="Smart Home Face Access Backend",
    description="Face recognition door access module for Design and Build smart home project.",
    version="1.0.0",
)

ensure_directories()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.include_router(person_router)
app.include_router(face_router)
app.include_router(door_router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error(exc.code, exc.message, exc.data),
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content=error(4000, "request parameter error", None),
    )


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    message = str(exc.detail) if exc.detail else "request parameter error"
    code = 4001 if exc.status_code == 404 else 4000
    return JSONResponse(status_code=exc.status_code, content=error(code, message, None))


@app.exception_handler(Exception)
async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content=error(5000, "backend internal error", None))


@app.get("/")
def index() -> RedirectResponse:
    return RedirectResponse(url="/face/register")


@app.get("/face/register")
def register_page(request: Request):
    return templates.TemplateResponse("face_register.html", {"request": request})


@app.get("/face/verify")
def verify_page(request: Request):
    return templates.TemplateResponse("face_verify.html", {"request": request})


@app.get("/face/logs")
def logs_page(request: Request):
    return templates.TemplateResponse("access_logs.html", {"request": request})
