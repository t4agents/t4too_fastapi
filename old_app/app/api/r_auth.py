from fastapi import APIRouter, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.db_async import get_db
from app.service.ser_auth import register_user

authRou = APIRouter()
security = HTTPBearer()


@authRou.post("/register")
async def register(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    decoded = request.state.user
    return await register_user(decoded, db)