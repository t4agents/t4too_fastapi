import time, httpx
from typing import Any, Dict
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt as jose_jwt
from jose import jwk as jose_jwk
from jose.exceptions import JWTError

from app.config import get_settings_singleton

_JWKS_CACHE: Dict[str, Any] | None = None
_JWKS_CACHE_TS: float | None = None
_JWKS_TTL_SECONDS = 3600

_security = HTTPBearer(auto_error=False)

async def _fetch_jwks() -> Dict[str, Any]:
    settings = get_settings_singleton()
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(settings.JWKS_URL)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict) or "keys" not in data:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid JWKS response.",)
        return data


async def _get_jwks_cached() -> Dict[str, Any]:
    global _JWKS_CACHE, _JWKS_CACHE_TS
    now = time.time()
    if _JWKS_CACHE and _JWKS_CACHE_TS and (now - _JWKS_CACHE_TS) < _JWKS_TTL_SECONDS: return _JWKS_CACHE
    _JWKS_CACHE = await _fetch_jwks()
    _JWKS_CACHE_TS = now
    return _JWKS_CACHE


def _find_jwk(jwks: Dict[str, Any], kid: str | None) -> Dict[str, Any] | None:
    keys = jwks.get("keys", [])
    if not isinstance(keys, list):return None
    if kid:
        for key in keys:
            if key.get("kid") == kid:
                return key
    if keys:return keys[0]
    return None


async def get_jwks_decoded(credentials: HTTPAuthorizationCredentials = Depends(_security),) -> Dict[str, Any]:
    if not credentials or credentials.scheme.lower() != "bearer": raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Missing bearer token.",)
   
    token = credentials.credentials
   
    try:
        header = jose_jwt.get_unverified_header(token)
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token header.",) from exc

    jwks = await _get_jwks_cached()
    jwk = _find_jwk(jwks, header.get("kid"))
    if not jwk: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Signing key not found.",)

    try:
        jwk_key = jose_jwk.construct(jwk)
        key = jwk_key.to_pem().decode("utf-8")
        settings = get_settings_singleton()
        decoded = jose_jwt.decode(
            token,
            key=key,
            algorithms=settings.JWKS_ALG,
            audience=settings.JWKS_AUD,
            issuer=settings.JWKS_ISS,
        )
        return decoded
    except JWTError: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token validation failed.")




async def get_zjwt(decoded: Dict[str, Any] = Depends(get_jwks_decoded)) -> dict[str, Any]:
    user_id = decoded.get("sub") or decoded.get("id")
    app_metadata = decoded.get("app_metadata")
    user_metadata = decoded.get("user_metadata")

    if not isinstance(app_metadata, dict):app_metadata = {}
    if not isinstance(user_metadata, dict):user_metadata = {}

    return {
        "zuid": user_id,
        "app_metadata": app_metadata,
        "user_metadata": user_metadata,
    }

    # print("1------------", zjwt["zuid"])
    # print("2------------", zjwt["app_metadata"]["sba_ten_id"])
    # print("3------------", zjwt["user_metadata"]["avatar"])
    # print("4------------", zjwt["user_metadata"]["sbu_name"])
    # print("5------------", zjwt["user_metadata"]["display_name"])
    # print("6------------", zjwt["user_metadata"]["sbu_client_id"])
