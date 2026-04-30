from dataclasses import dataclass
from uuid import UUID

import jwt
import requests
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal


@dataclass
class UserContext:
    user_id: UUID
    owner_id: UUID


_jwks_cache: dict = {}


def _resolve_token_owner(authorization: str) -> UUID | None:
    if not settings.supabase_jwt_issuer:
        return None
    if not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        return None

    jwks = _jwks_cache.get("jwks")
    if not jwks:
        jwks_url = settings.supabase_jwt_issuer.rstrip("/") + "/.well-known/jwks.json"
        jwks = requests.get(jwks_url, timeout=5).json()
        _jwks_cache["jwks"] = jwks

    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    key = None
    for item in jwks.get("keys", []):
        if item.get("kid") == kid:
            key = jwt.algorithms.RSAAlgorithm.from_jwk(item)
            break
    if not key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token key")

    payload = jwt.decode(
        token,
        key=key,
        algorithms=["RS256"],
        audience=settings.supabase_jwt_audience,
        issuer=settings.supabase_jwt_issuer,
    )
    sub = payload.get("sub")
    if not sub:
        return None
    return UUID(sub)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    x_owner_id: str | None = Header(default=None, alias="X-Owner-Id"),
    authorization: str | None = Header(default="", alias="Authorization"),
) -> UserContext:
    if authorization:
        try:
            owner = _resolve_token_owner(authorization)
            if owner:
                return UserContext(user_id=owner, owner_id=owner)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized token") from exc

    # Production note: replace with strict Supabase JWT verification middleware.
    if x_owner_id:
        try:
            parsed = UUID(x_owner_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid X-Owner-Id UUID") from exc
        return UserContext(user_id=parsed, owner_id=parsed)

    if settings.app_env.lower() in {"dev", "local"}:
        demo = UUID("00000000-0000-0000-0000-000000000001")
        return UserContext(user_id=demo, owner_id=demo)

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


CurrentUser = Depends(get_current_user)
DbSession = Depends(get_db)
