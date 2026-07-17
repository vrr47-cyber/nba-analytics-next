from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api import health, meta, players, status, teams
from backend.app.core.config import get_settings
from backend.app.core.errors import application_error_handler
from backend.app.core.logging import configure_logging
from backend.app.core.request_id import RequestIdMiddleware
from backend.app.services.application import build_services


def create_app() -> FastAPI:
    settings = get_settings()
    settings.validate_runtime()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.services = build_services(settings)
        yield
        engine = app.state.services.engine
        if engine is not None:
            engine.dispose()

    app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["*"], allow_headers=["*"])
    app.add_exception_handler(Exception, application_error_handler)
    app.include_router(health.router)
    app.include_router(status.router)
    app.include_router(meta.router)
    app.include_router(teams.router)
    app.include_router(players.router)
    return app


app = create_app()
