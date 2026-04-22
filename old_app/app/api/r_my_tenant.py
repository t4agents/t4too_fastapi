from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from app.db.db_async import get_db
from app.schemas.sch_my_tenant import MyTenantCreate, MyTenantUpdate, MyTenantResponse
from app.service.ser_my_tenant import (
    create_my_tenant,
    get_my_tenant,
    list_my_tenants,
    update_my_tenant,
    delete_my_tenant,
    get_tenant_by_name,
    get_tenant_count,
)

myTenantRou = APIRouter()


@myTenantRou.post("", response_model=MyTenantResponse)
async def create(
    data: MyTenantCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new tenant."""
    return await create_my_tenant(data, db)


@myTenantRou.get("/{tenant_id}", response_model=MyTenantResponse)
async def get(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get tenant by ID."""
    return await get_my_tenant(tenant_id, db)


@myTenantRou.get("", response_model=List[MyTenantResponse])
async def list(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """List all tenants with pagination."""
    return await list_my_tenants(db, skip=skip, limit=limit)


@myTenantRou.get("/search/by-name", response_model=MyTenantResponse)
async def search_by_name(
    name: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
):
    """Search tenant by name."""
    tenant = await get_tenant_by_name(name, db)
    if not tenant:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


@myTenantRou.put("/{tenant_id}", response_model=MyTenantResponse)
async def update(
    tenant_id: UUID,
    data: MyTenantUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a tenant."""
    return await update_my_tenant(tenant_id, data, db)


@myTenantRou.delete("/{tenant_id}")
async def delete(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a tenant."""
    return await delete_my_tenant(tenant_id, db)


@myTenantRou.get("/stats/count")
async def get_count(
    db: AsyncSession = Depends(get_db),
):
    """Get total number of tenants."""
    count = await get_tenant_count(db)
    return {"total": count}
