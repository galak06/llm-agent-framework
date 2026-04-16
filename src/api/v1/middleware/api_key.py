import hmac

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from src.core.config import Settings, get_settings

api_key_header = APIKeyHeader(name='X-API-Key', auto_error=False)
admin_key_header = APIKeyHeader(name='X-Admin-Key', auto_error=False)


def require_widget_key(
    key: str | None = Security(api_key_header),
    settings: Settings = Depends(get_settings),
) -> None:
    if not key or not hmac.compare_digest(key, settings.widget_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid or missing API key',
        )


def require_admin_key(
    key: str | None = Security(admin_key_header),
    settings: Settings = Depends(get_settings),
) -> None:
    if not key or not hmac.compare_digest(key, settings.admin_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid or missing admin API key',
        )
