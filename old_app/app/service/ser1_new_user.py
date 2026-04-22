from uuid import uuid4

from fastapi import HTTPException, status

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import m_be, m_user, m_user_client, m_zme
from app.db.seeds.seed_payroll_schedules import ensure_payroll_schedules_for_be

async def new_user(decoded: dict, db: AsyncSession) -> dict[str, str | None]:
    # firebase_uid is extracted via dependency # decoded contains the full Firebase token payload
    firebase_uid = decoded.get("uid") or decoded.get("user_id") or decoded.get("sub")
    email = decoded.get("email") or f"t4agents@gmail.com"  # default email if not provided
    name  = decoded.get("name") or "T4 Agents"  # default name if not provided
    first_name = "T4"
    last_name = "Agents"
    phone = "332-203-4114"  # default phone, can be updated later
    position = "CPA"  # default position, can be updated later
    facebook = "https://facebook.com/t4agents"  # default Facebook URL, can be updated later
    twitter = "https://twitter.com/t4agents"  # default Twitter URL, can be updated later
    github = "https://github.com/t4agents"  # default GitHub URL, can be updated later
    reddit = "https://reddit.com/u/t4agents"  # default
    
    country = "Canada"  # default location, can be updated later
    state = "Ontario"  # default state, can be updated later
    pin = "3322034114"  # default pin, can be updated later
    zip = "M5V 2T6"  # default zip, can be updated later
    tax_no = "T4AGENTS123"  # default tax number, can be
   
    
    if not firebase_uid:  raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    # check existing
    result = await db.execute(select(m_zme.ZMeDB).where(m_zme.ZMeDB.firebase_uid == firebase_uid))
    existing = result.scalar_one_or_none()

    if existing:return {"message": "already registered",}

    ten_be_user_id = uuid4()
    tenant_id = str(ten_be_user_id)
    await db.execute(
        text("select set_config('t4rls.tid', :tenant_id, true)"),
        {"tenant_id": tenant_id},
    )
    
    user = m_user.UserDB(
        firebase_uid=firebase_uid,

        id     =ten_be_user_id,
        biz_id =ten_be_user_id,
        ten_id =ten_be_user_id,
        
        owner_id=ten_be_user_id,  # required by your design

        email=email,
        name=name,
        country=country,
        phone=phone,
        position=position,
        facebook=facebook,
        twitter=twitter,
        github=github,
        reddit=reddit,
        state=state,
        pin=pin,
        zip=zip,
        tax_no=tax_no,
        first_name=first_name,
        last_name=last_name,
    )


    be = m_be.BizEntity(
        id      =ten_be_user_id,
        ten_id  =ten_be_user_id,
        owner_id=ten_be_user_id,  # required by your design
        biz_id =ten_be_user_id,
        
        type="ME",
        email=email,
        name="My Business",
        country=country,
        phone=phone,        
    )


    user_client = m_user_client.UserClient(
        user_id=ten_be_user_id,
        biz_id=ten_be_user_id,
        ten_id=ten_be_user_id,
    )
    

    myuserten = m_zme.ZMeDB(
        id      =   ten_be_user_id,
        ten_id  =   ten_be_user_id,
        biz_id  =   ten_be_user_id,  # required by your design
        owner_id=   ten_be_user_id,  # required by your design       
        
        firebase_uid=firebase_uid,
    )


    db.add(user)
    db.add(myuserten)
    db.add(be)
    db.add(user_client)

    await ensure_payroll_schedules_for_be(
        db,
        ten_id=ten_be_user_id,
        biz_id=ten_be_user_id,
        owner_id=ten_be_user_id,
        created_by=ten_be_user_id,
    )

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="User already exists (firebase_uid or email conflict).",
        )

    return {"message": "registered", "user_id": str(ten_be_user_id), "ten_id": str(ten_be_user_id)}
