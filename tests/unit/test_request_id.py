from __future__ import annotations

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.api.v1.middleware.request_id import REQUEST_ID_HEADER, RequestIDMiddleware


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)

    @app.get('/test')
    async def test_endpoint() -> dict:
        return {'ok': True}

    return app


@pytest.mark.asyncio
async def test_generates_request_id(app: FastAPI) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        response = await client.get('/test')
    assert REQUEST_ID_HEADER in response.headers
    assert len(response.headers[REQUEST_ID_HEADER]) > 0


@pytest.mark.asyncio
async def test_passes_through_existing_id(app: FastAPI) -> None:
    custom_id = 'my-custom-request-id'
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        response = await client.get('/test', headers={REQUEST_ID_HEADER: custom_id})
    assert response.headers[REQUEST_ID_HEADER] == custom_id
