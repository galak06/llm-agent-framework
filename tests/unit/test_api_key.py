from __future__ import annotations

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient

from src.api.v1.middleware.api_key import require_widget_key
from src.core.config import Settings


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    app = FastAPI()

    @app.get('/protected', dependencies=[Depends(require_widget_key)])
    async def protected() -> dict:
        return {'ok': True}

    # Override get_settings to use test settings
    from src.core.config import get_settings

    app.dependency_overrides[get_settings] = lambda: settings
    return app


@pytest.mark.asyncio
async def test_missing_key_returns_401(app: FastAPI) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        response = await client.get('/protected')
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_wrong_key_returns_401(app: FastAPI) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        response = await client.get('/protected', headers={'X-API-Key': 'wrong-key'})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_correct_key_passes(app: FastAPI) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        response = await client.get('/protected', headers={'X-API-Key': 'test-widget-key'})
    assert response.status_code == 200
    assert response.json() == {'ok': True}
