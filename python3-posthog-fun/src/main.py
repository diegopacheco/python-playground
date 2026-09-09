import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from posthog import Posthog

from analytics import Analytics
from api import build_router
from catalog import CATALOG
from config import load_settings
from posthog_client import posthog_client
from rentals import RentalService
from rollup import RollupJob
from store import Store
from workers import IntervalWorker


def create_app(posthog: Posthog | None = posthog_client) -> FastAPI:
    settings = load_settings()
    store = Store(CATALOG)
    analytics = Analytics(posthog, store)
    service = RentalService(store, settings, analytics)
    rollup = RollupJob(store, settings, analytics)

    workers = (
        IntervalWorker("deadline-scan", settings.deadline_scan_seconds, service.scan_deadlines),
        IntervalWorker("idle-rollup", settings.rollup_interval_minutes * 60, rollup.run),
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        for worker in workers:
            worker.start()
        yield
        for worker in workers:
            worker.stop()
        if posthog is not None:
            posthog.shutdown()

    app = FastAPI(title="DVD Rental API", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(build_router(store, settings, service, analytics))
    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=os.getenv("API_HOST", "127.0.0.1"),
        port=int(os.getenv("API_PORT", "8000")),
    )
