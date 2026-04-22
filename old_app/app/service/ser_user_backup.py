from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.db.models.m_user import UserDB
from app.schemas.sch_user import MyUserCreate, MyUserUpdate


async def create_my_user(data: MyUserCreate, db: AsyncSession) -> UserDB:
    """Create a new user."""
    user = UserDB(**data.model_dump())
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def get_user_profile(uid: UUID, db: AsyncSession) -> UserDB:
    """Get user by ID."""
    result = await db.execute(
        select(UserDB).where(UserDB.id == uid)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


async def list_my_users(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> List[UserDB]:
    """List all users with pagination."""
    result = await db.execute(
        select(UserDB).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def update_my_user(
    uid: UUID, data: MyUserUpdate, db: AsyncSession
) -> UserDB:
    print(f"Attempting to update user with UID: {uid}")
    
    user = await get_user_profile(uid, db)
    print(f"Updating user {uid} with data: {data} and current user data: {user}")

    # Update only provided fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def delete_my_user(uid: UUID, db: AsyncSession) -> dict:
    """Delete a user by Firebase UID."""
    user = await get_user_profile(uid, db)

    await db.delete(user)
    await db.flush()
    return {"detail": "User deleted successfully"}


async def get_user_by_email(email: str, db: AsyncSession) -> Optional[UserDB]:
    """Get user by email."""
    result = await db.execute(
        select(UserDB).where(UserDB.email == email)
    )
    return result.scalars().first()


async def get_user_count(db: AsyncSession) -> int:
    """Get total number of users."""
    from sqlalchemy import func
    result = await db.execute(select(func.count(UserDB.id)))
    return result.scalar_one()









from uuid import uuid4
from alembic.util import status
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.core.firebase_auth import core_verify_firebase_token
from app.db.models.m_user import UserDB
from app.db.models.m_user_client import UserClient
from app.db.models.m_be import BizEntity 


async def save_profile_user_biz_ten(decoded: dict, db: AsyncSession) -> dict[str, str | None]:
    # firebase_uid is extracted via dependency
    # decoded contains the full Firebase token payload
    firebase_uid = decoded.get("uid") or decoded.get("user_id") or decoded.get("sub")
    email = decoded.get("email") or f"t4agents@gmail.com"  # default email if not provided
    name  = decoded.get("name", "")
    location = "Canada"  # default location, can be updated later
    state = "Ontario"  # default state, can be updated later
    pin = "3322034114"  # default pin, can be updated later
    
    
    if not firebase_uid:  raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    # check existing
    result = await db.execute(
        select(UserDB).where(UserDB.firebase_uid == firebase_uid)
    )
    existing = result.scalar_one_or_none()

    if existing:
        return {
            "message": "already registered",
            "user_id": str(existing.id),
            "ten_id": str(existing.id) if existing.id else None,
        }


    ten_be_user_id = uuid4()
    
    user = UserDB(
        id      =ten_be_user_id,
        ten_id  =ten_be_user_id,
        biz_id  =ten_be_user_id,  # required by your design
        owner_id=ten_be_user_id,  # required by your design
        firebase_uid=firebase_uid,

        email=email,
        name=name,
        country=location,
    )


    be = BizEntity(
        id      =ten_be_user_id,
        ten_id  =ten_be_user_id,
        biz_id  =ten_be_user_id,  # required by your design
        owner_id=ten_be_user_id,  # required by your design
        
        type="ME",
        email=email,
        name=name,
    )


    myuserten = UserClient(
        user_id=ten_be_user_id,
        biz_id=ten_be_user_id,
        ten_id=ten_be_user_id,
    )

    db.add(user)
    db.add(be)
    db.add(myuserten)

    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="User already exists (firebase_uid or email conflict).",
        )

    return {"message": "registered", "user_id": str(ten_be_user_id), "ten_id": str(ten_be_user_id)}
