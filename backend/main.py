from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from core.config import settings
from db.session import engine
from apis.base import api_router
from apps.base import app_router


BASE_DIR = Path(__file__).resolve().parent


def include_routers(app):
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
    app.include_router(app_router)
    app.include_router(api_router)


def start_app():
    app = FastAPI(title=settings.PROJECT_TITLE, version=settings.PROJECT_VERSION)
    include_routers(app)
    return app


app = start_app()
