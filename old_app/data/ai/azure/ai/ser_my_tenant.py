from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.db.models.my_tenant import MyTenant
from app.schemas.sch_my_tenant import MyTenantCreate, MyTenantUpdate


async def create_my_tenant(data: MyTenantCreate, db: AsyncSession) -> MyTenant:
    """Create a new tenant."""
    tenant = MyTenant(**data.model_dump())
    db.add(tenant)
    await db.flush()
    await db.refresh(tenant)
    return tenant


async def get_my_tenant(tenant_id: UUID, db: AsyncSession) -> MyTenant:
    """Get tenant by ID."""
    result = await db.execute(
        select(MyTenant).where(MyTenant.id == tenant_id)
    )
    tenant = result.scalars().first()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return tenant


async def list_my_tenants(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> List[MyTenant]:
    """List all tenants with pagination."""
    result = await db.execute(
        select(MyTenant).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def update_my_tenant(
    tenant_id: UUID, data: MyTenantUpdate, db: AsyncSession
) -> MyTenant:
    """Update an existing tenant."""
    tenant = await get_my_tenant(tenant_id, db)

    # Update only provided fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tenant, field, value)

    db.add(tenant)
    await db.flush()
    await db.refresh(tenant)
    return tenant


async def delete_my_tenant(tenant_id: UUID, db: AsyncSession) -> dict:
    """Delete a tenant by ID."""
    tenant = await get_my_tenant(tenant_id, db)

    await db.delete(tenant)
    await db.flush()
    return {"detail": "Tenant deleted successfully"}


async def get_tenant_by_name(name: str, db: AsyncSession) -> Optional[MyTenant]:
    """Get tenant by name."""
    result = await db.execute(
        select(MyTenant).where(MyTenant.name == name)
    )
    return result.scalars().first()


async def get_tenant_count(db: AsyncSession) -> int:
    """Get total number of tenants."""
    result = await db.execute(select(MyTenant))
    return len(result.scalars().all())
