"""FastAPI application factory.

The application is created through a factory (`--factory` for uvicorn) so tests
can inject settings without importing a module that demands a configured
environment.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import api, health
from app.config import Settings, get_settings
from app.db import create_engine, create_session_factory


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    await app.state.engine.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()

    app = FastAPI(
        title="proy-nuevo backend",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.settings = resolved
    app.state.engine = create_engine(resolved.database_url)
    app.state.session_factory = create_session_factory(app.state.engine)

    app.include_router(health.router)
    app.include_router(api.router, prefix="/api/v1")

    return app
