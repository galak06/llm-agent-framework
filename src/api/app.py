from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api.v1.middleware.rate_limit import RateLimitMiddleware
from src.api.v1.middleware.request_id import RequestIDMiddleware
from src.api.v1.routes import admin, chat, chatflows, health, prediction
from src.core.config import Settings, get_settings
from src.core.container import ServiceContainer
from src.core.logging import configure_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    """Application factory."""
    if settings is None:
        settings = get_settings()

    configure_logging(settings)

    # Force debug off in production
    is_debug = settings.debug and settings.app_env != 'production'

    app = FastAPI(
        title=settings.app_name,
        debug=is_debug,
        docs_url='/docs' if is_debug else None,
        redoc_url='/redoc' if is_debug else None,
    )

    # Service container — shared across all requests
    app.state.container = ServiceContainer(settings)

    # Middleware (order matters — outermost first)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(RateLimitMiddleware, settings=settings)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=['GET', 'POST', 'PUT'],
        allow_headers=['Content-Type', 'X-API-Key', 'X-Admin-Key', 'X-Request-ID'],
    )

    # Static widget files (no-cache in dev for hot reload)
    widget_dir = Path(__file__).resolve().parent.parent.parent / 'widget'
    if widget_dir.is_dir():
        app.mount('/widget', StaticFiles(directory=str(widget_dir), html=True), name='widget')

    # Routes
    prefix = f'/api/{settings.api_version}'
    app.include_router(health.router, prefix=prefix)
    app.include_router(chat.router, prefix=prefix)
    app.include_router(admin.router, prefix=prefix)
    app.include_router(prediction.router, prefix=prefix)
    app.include_router(chatflows.router, prefix=prefix)

    return app
