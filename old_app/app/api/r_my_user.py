from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from app.db.db_async import get_db
from app.schemas.sch_my_user import MyUserCreate, MyUserUpdate, MyUserResponse
from app.service.ser_my_user import (
    create_my_user,
    get_my_user,
    list_my_users,
    update_my_user,
    delete_my_user,
    get_user_by_email,
    get_user_count,
)

myUserRou = APIRouter()

@myUserRou.post("", response_model=MyUserResponse)
async def create(
    data: MyUserCreate,
    db: AsyncSession = Depends(get_db),
):
    return await create_my_user(data, db)

@myUserRou.get("/{user_id}", response_model=MyUserResponse)
async def get(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    return await get_my_user(user_id, db)

@myUserRou.get("", response_model=List[MyUserResponse])
async def list(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    return await list_my_users(db, skip=skip, limit=limit)

@myUserRou.get("/search/by-email", response_model=MyUserResponse)
async def search_by_email(
    email: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_email(email, db)
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")
    return user

@myUserRou.put("/{user_id}", response_model=MyUserResponse)
async def update(
    user_id: UUID,
    data: MyUserUpdate,
    db: AsyncSession = Depends(get_db),
):
    return await update_my_user(user_id, data, db)

@myUserRou.delete("/{user_id}")
async def delete(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    return await delete_my_user(user_id, db)

@myUserRou.get("/stats/count")
async def get_count(
    db: AsyncSession = Depends(get_db),
):
    count = await get_user_count(db)
    return {"total": count}
