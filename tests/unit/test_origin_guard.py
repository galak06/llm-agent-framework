from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from src.api.v1.middleware.origin_guard import require_allowed_origin
from src.core.config import Settings


def _make_request(origin: str | None, path: str = '/api/v1/prediction/nalla') -> Any:
    headers = {'origin': origin} if origin is not None else {}
    return SimpleNamespace(headers=headers, url=SimpleNamespace(path=path))


def _make_container(allowed: list[str]) -> Any:
    container = MagicMock()
    container.settings = Settings(
        _env_file=None,
        widget_api_key='test-key-1234',
        admin_api_key='test-key-1234',
        anthropic_api_key='sk-ant-test',
        database_url='postgresql+asyncpg://x',
        widget_allowed_origins=allowed,
    )
    return container


@pytest.mark.asyncio
async def test_empty_allowlist_is_noop() -> None:
    await require_allowed_origin(_make_request(origin=None), _make_container([]))
    await require_allowed_origin(_make_request(origin='https://evil.com'), _make_container([]))


@pytest.mark.asyncio
async def test_matching_origin_allowed() -> None:
    await require_allowed_origin(
        _make_request(origin='https://dogfoodandfun.com'),
        _make_container(['https://dogfoodandfun.com']),
    )


@pytest.mark.asyncio
async def test_mismatched_origin_rejected() -> None:
    with pytest.raises(HTTPException) as exc:
        await require_allowed_origin(
            _make_request(origin='https://evil.com'),
            _make_container(['https://dogfoodandfun.com']),
        )
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_missing_origin_rejected_when_allowlist_set() -> None:
    with pytest.raises(HTTPException) as exc:
        await require_allowed_origin(
            _make_request(origin=None),
            _make_container(['https://dogfoodandfun.com']),
        )
    assert exc.value.status_code == 403
