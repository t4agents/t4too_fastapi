from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.firebase_jwt import verify_firebase_token
from app.db.models.my_user import MyUser
from app.db.models.my_tenant import MyTenant


async def register_user(id_token: str, db: AsyncSession):


    decoded = verify_firebase_token(id_token)
    print("DECODED:", decoded)

    # firebase_uid = decoded["uid"]
    firebase_uid = decoded.get("user_id") or decoded.get("sub")
    email = decoded.get("email")
    name = decoded.get("name", "")

    # check existing
    result = await db.execute(
        select(MyUser).where(MyUser.firebase_uid == firebase_uid)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    # create org_id
    new_org_id = uuid4()

    org = MyTenant(
        id=new_org_id,
        org_id=new_org_id,  # required by your design
        name=email or "New Organization",
        type="company",
    )

    user = MyUser(
        org_id=new_org_id,
        firebase_uid=firebase_uid,
        email=email,
        name=name,
    )

    db.add(org)
    db.add(user)

    await db.commit()

    return {"message": "registered"}