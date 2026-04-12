import time
import logging
from typing import Any, Dict

import httpx
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
_log = logging.getLogger(__name__)
_http_log = logging.getLogger("app.http")


async def _fetch_jwks() -> Dict[str, Any]:
    settings = get_settings_singleton()
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(settings.JWKS_URL)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict) or "keys" not in data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid JWKS response.",
            )
        return data


async def _get_jwks_cached() -> Dict[str, Any]:
    global _JWKS_CACHE, _JWKS_CACHE_TS
    now = time.time()
    if _JWKS_CACHE and _JWKS_CACHE_TS and (now - _JWKS_CACHE_TS) < _JWKS_TTL_SECONDS:
        return _JWKS_CACHE
    _JWKS_CACHE = await _fetch_jwks()
    _JWKS_CACHE_TS = now
    return _JWKS_CACHE


def _find_jwk(jwks: Dict[str, Any], kid: str | None) -> Dict[str, Any] | None:
    keys = jwks.get("keys", [])
    if not isinstance(keys, list):
        return None
    if kid:
        for key in keys:
            if key.get("kid") == kid:
                return key
    if keys:
        return keys[0]
    return None


async def get_jwks_decoded(
    credentials: HTTPAuthorizationCredentials = Depends(_security),
) -> Dict[str, Any]:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
        )
    token = credentials.credentials
    _http_log.info("auth: received bearer token=%s", token)
    try:
        header = jose_jwt.get_unverified_header(token)
        try:
            unverified_claims = jose_jwt.get_unverified_claims(token)
        except JWTError:
            unverified_claims = {}
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token header.",
        ) from exc
    _http_log.info(
        "auth: unverified header=%s claims=%s",
        header,
        unverified_claims,
    )

    jwks = await _get_jwks_cached()
    jwk = _find_jwk(jwks, header.get("kid"))
    if not jwk:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Signing key not found.",
        )

    try:
        jwk_key = jose_jwk.construct(jwk)
        key = jwk_key.to_pem().decode("utf-8")
        settings = get_settings_singleton()
        _http_log.info(
            "auth: validating token header=%s jwks_url=%s expected_iss=%s expected_aud=%s expected_alg=%s",
            header,
            settings.JWKS_URL,
            settings.JWKS_ISS,
            settings.JWKS_AUD,
            settings.JWKS_ALG,
        )
        decoded = jose_jwt.decode(
            token,
            key=key,
            algorithms=settings.JWKS_ALG,
            audience=settings.JWKS_AUD,
            issuer=settings.JWKS_ISS,
        )
        _http_log.info("auth: token validated claims=%s", decoded)
        return decoded
    except JWTError as exc:
        # Full diagnostics for auth failures (no signature verification here)
        try:
            unverified_claims = jose_jwt.get_unverified_claims(token)
        except JWTError:
            unverified_claims = {}
        settings = get_settings_singleton()
        _log.info(
            "JWT validation failed. token=%s header=%s claims=%s jwks_url=%s expected_iss=%s expected_aud=%s error=%s",
            token,
            header,
            unverified_claims,
            settings.JWKS_URL,
            settings.JWKS_ISS,
            settings.JWKS_AUD,
            str(exc),
        )
        _http_log.info(
            "auth: validation failed token=%s header=%s claims=%s jwks_url=%s expected_iss=%s expected_aud=%s error=%s",
            token,
            header,
            unverified_claims,
            settings.JWKS_URL,
            settings.JWKS_ISS,
            settings.JWKS_AUD,
            str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed.",
        ) from exc
