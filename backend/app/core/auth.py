"""
Autenticación por API Key para el MVP del piloto.

Mecanismo: header X-API-Key validado contra la variable de entorno ZUVRA_API_KEY.
Simple, sin overhead, suficiente para un piloto con un cliente conocido.
"""
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import get_settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(api_key: str | None = Security(_api_key_header)) -> str:
    settings = get_settings()
    expected = settings.ZUVRA_API_KEY
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key no configurada en el servidor",
        )
    if not api_key or api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key inválida o ausente",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return api_key
