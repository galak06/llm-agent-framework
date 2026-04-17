from __future__ import annotations

import base64

import pytest
from fastapi import HTTPException

from src.api.v1.routes.prediction import FlowiseUpload, _parse_uploads, _split_data_url
from src.core.config import Settings

PNG_BYTES = b'\x89PNG\r\n\x1a\n' + b'\x00' * 64
PNG_B64 = base64.b64encode(PNG_BYTES).decode('ascii')
PNG_DATA_URL = f'data:image/png;base64,{PNG_B64}'


def test_parse_uploads_returns_empty_for_none(settings: Settings) -> None:
    assert _parse_uploads(None, settings) == []
    assert _parse_uploads([], settings) == []


def test_parse_uploads_decodes_data_url(settings: Settings) -> None:
    images = _parse_uploads([FlowiseUpload(data=PNG_DATA_URL, mime='image/png')], settings)

    assert len(images) == 1
    assert images[0].mime_type == 'image/png'
    assert images[0].data == PNG_BYTES


def test_parse_uploads_uses_fallback_mime_when_no_data_url(settings: Settings) -> None:
    images = _parse_uploads([FlowiseUpload(data=PNG_B64, mime='image/jpeg')], settings)

    assert images[0].mime_type == 'image/jpeg'
    assert images[0].data == PNG_BYTES


def test_parse_uploads_rejects_disallowed_mime(settings: Settings) -> None:
    gif_data_url = f'data:image/gif;base64,{PNG_B64}'
    with pytest.raises(HTTPException) as exc:
        _parse_uploads([FlowiseUpload(data=gif_data_url)], settings)
    assert exc.value.status_code == 400
    assert 'Unsupported' in exc.value.detail


def test_parse_uploads_rejects_too_many(settings: Settings) -> None:
    uploads = [FlowiseUpload(data=PNG_DATA_URL) for _ in range(settings.image_max_per_request + 1)]
    with pytest.raises(HTTPException) as exc:
        _parse_uploads(uploads, settings)
    assert exc.value.status_code == 400
    assert 'Too many' in exc.value.detail


def test_parse_uploads_rejects_oversize(settings: Settings) -> None:
    oversized = b'\x00' * (settings.image_max_bytes + 1)
    data_url = f'data:image/png;base64,{base64.b64encode(oversized).decode("ascii")}'
    with pytest.raises(HTTPException) as exc:
        _parse_uploads([FlowiseUpload(data=data_url)], settings)
    assert exc.value.status_code == 400
    assert 'size limit' in exc.value.detail


def test_parse_uploads_rejects_bad_base64(settings: Settings) -> None:
    with pytest.raises(HTTPException) as exc:
        _parse_uploads([FlowiseUpload(data='data:image/png;base64,!!!not-base64!!!')], settings)
    assert exc.value.status_code == 400
    assert 'Invalid base64' in exc.value.detail


def test_split_data_url_full_prefix() -> None:
    mime, payload = _split_data_url('data:image/webp;base64,YWJj', fallback_mime=None)
    assert mime == 'image/webp'
    assert payload == 'YWJj'


def test_split_data_url_bare_base64_uses_fallback() -> None:
    mime, payload = _split_data_url('YWJj', fallback_mime='image/jpeg')
    assert mime == 'image/jpeg'
    assert payload == 'YWJj'
