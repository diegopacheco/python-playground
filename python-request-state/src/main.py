import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from controller import router
from db import init_db
from middleware import request_state
from service import GameNotFound

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = os.environ.get("GAMES_DB_PATH", str(ROOT / "games.db"))


async def not_found(request: Request, error: GameNotFound) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": f"game {error} not found", "request_id": request.state.request_id},
    )


def create_app(db_path: str = DB_PATH) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await init_db(db_path)
        yield

    app = FastAPI(title="Games CRUD", lifespan=lifespan)
    app.middleware("http")(request_state(db_path))
    app.add_exception_handler(GameNotFound, not_found)
    app.include_router(router)
    app.mount("/", StaticFiles(directory=ROOT / "static", html=True), name="static")
    return app
