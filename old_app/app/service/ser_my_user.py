from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.db.models.my_user import MyUser
from app.schemas.sch_my_user import MyUserCreate, MyUserUpdate

async def create_my_user(data: MyUserCreate, db: AsyncSession) -> MyUser:
    user = MyUser(**data.model_dump())
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def get_my_user(user_id: UUID, db: AsyncSession) -> MyUser:
    result = await db.execute(
        select(MyUser).where(MyUser.id == user_id, MyUser.is_deleted != True)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

async def list_my_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[MyUser]:
    result = await db.execute(
        select(MyUser).where(MyUser.is_deleted != True).offset(skip).limit(limit)
    )
    return result.scalars().all()

async def update_my_user(user_id: UUID, data: MyUserUpdate, db: AsyncSession) -> MyUser:
    user = await get_my_user(user_id, db)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def delete_my_user(user_id: UUID, db: AsyncSession) -> dict:
    user = await get_my_user(user_id, db)
    user.is_deleted = True
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"detail": "User soft-deleted successfully"}

async def get_user_by_email(email: str, db: AsyncSession) -> Optional[MyUser]:
    result = await db.execute(
        select(MyUser).where(MyUser.email == email, MyUser.is_deleted != True)
    )
    return result.scalars().first()

async def get_user_count(db: AsyncSession) -> int:
    result = await db.execute(select(MyUser).where(MyUser.is_deleted != True))
    return len(result.scalars().all())
