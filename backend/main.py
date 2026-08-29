from fastapi import FastAPI
from core.config import settings
from db.session import engine
from apis.base import api_router

def include_routers(app):
    app.include_router(api_router)

def start_app():
    app = FastAPI(title=settings.PROJECT_TITLE, version=settings.PROJECT_VERSION)
    include_routers(app)
    return app

app = start_app()

@app.get("/")
def hello():
    return {"msg": "Hello FastAPI"}