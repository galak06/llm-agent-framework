from __future__ import annotations

import base64
from io import BytesIO

import pytest
from fastapi import HTTPException
from PIL import Image

from src.api.v1.routes.prediction import (
    FlowiseUpload,
    _parse_uploads,
    _sanitize_image_bytes,
    _split_data_url,
)
from src.core.config import Settings


def _png_bytes(size: tuple[int, int] = (8, 8), color: str = 'red') -> bytes:
    img = Image.new('RGB', size, color=color)
    buf = BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()


def _jpeg_with_exif() -> bytes:
    """A JPEG carrying EXIF tags (the kind we want to strip)."""
    img = Image.new('RGB', (8, 8), color='blue')
    exif = img.getexif()
    exif[0x010E] = 'sensitive caption'  # ImageDescription
    exif[0x010F] = 'Camera Manufacturer'  # Make
    exif[0x0110] = 'Camera Model'  # Model
    buf = BytesIO()
    img.save(buf, format='JPEG', exif=exif)
    return buf.getvalue()


PNG_BYTES = _png_bytes()
PNG_B64 = base64.b64encode(PNG_BYTES).decode('ascii')
PNG_DATA_URL = f'data:image/png;base64,{PNG_B64}'


def test_parse_uploads_returns_empty_for_none(settings: Settings) -> None:
    assert _parse_uploads(None, settings) == []
    assert _parse_uploads([], settings) == []


def test_parse_uploads_decodes_data_url(settings: Settings) -> None:
    images = _parse_uploads([FlowiseUpload(data=PNG_DATA_URL, mime='image/png')], settings)

    assert len(images) == 1
    assert images[0].mime_type == 'image/png'
    # Bytes round-trip through PIL so they won't equal the input exactly,
    # but the result must still decode as a valid PNG.
    assert Image.open(BytesIO(images[0].data)).format == 'PNG'


def test_parse_uploads_uses_fallback_mime_when_no_data_url(settings: Settings) -> None:
    jpeg = _jpeg_with_exif()
    jpeg_b64 = base64.b64encode(jpeg).decode('ascii')
    images = _parse_uploads([FlowiseUpload(data=jpeg_b64, mime='image/jpeg')], settings)

    assert images[0].mime_type == 'image/jpeg'
    assert Image.open(BytesIO(images[0].data)).format == 'JPEG'


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


def test_parse_uploads_rejects_corrupt_image(settings: Settings) -> None:
    """Bytes that decode as base64 but aren't a valid image must be rejected."""
    junk = base64.b64encode(b'\x89PNG\r\n\x1a\n' + b'\x00' * 64).decode('ascii')
    with pytest.raises(HTTPException) as exc:
        _parse_uploads(
            [FlowiseUpload(data=f'data:image/png;base64,{junk}', mime='image/png')], settings
        )
    assert exc.value.status_code == 400
    assert 'Invalid or corrupt' in exc.value.detail


def test_sanitize_strips_exif() -> None:
    """The sanitizer must drop EXIF blocks before bytes leave the API."""
    raw = _jpeg_with_exif()
    # Sanity check: the raw JPEG carries EXIF before sanitization.
    assert Image.open(BytesIO(raw)).getexif()

    cleaned = _sanitize_image_bytes(raw, 'image/jpeg')
    cleaned_exif = Image.open(BytesIO(cleaned)).getexif()

    # Pillow returns an empty IFD object when no EXIF is present.
    assert dict(cleaned_exif) == {}


def test_sanitize_rejects_bad_bytes() -> None:
    with pytest.raises(HTTPException) as exc:
        _sanitize_image_bytes(b'not an image', 'image/png')
    assert exc.value.status_code == 400


def test_split_data_url_full_prefix() -> None:
    mime, payload = _split_data_url('data:image/webp;base64,YWJj', fallback_mime=None)
    assert mime == 'image/webp'
    assert payload == 'YWJj'


def test_split_data_url_bare_base64_uses_fallback() -> None:
    mime, payload = _split_data_url('YWJj', fallback_mime='image/jpeg')
    assert mime == 'image/jpeg'
    assert payload == 'YWJj'
