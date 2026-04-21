from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_zjwt
from app.db.conn.db_async import get_db_rls
from app.db.models.inv.i_tem import ItemDB
from app.schemas.sch_item import ItemCreate, ItemOut
from app.service.ser_item import create_or_update_item, fetch_items

itemRou = APIRouter()


def _to_out(item: ItemDB) -> ItemOut:
    return ItemOut(
        id=item.id,
        item_number=item.item_number,
        item_name=item.item_name,
        item_rate=item.item_rate,
        item_unit_of_measure=item.item_unit_of_measure,
        item_unit=item.item_unit,
        item_sku=item.item_sku,
        item_description=item.item_description,
        item_quantity=item.item_quantity,
        item_note=item.item_note,
        item_amount=item.item_amount,
    )


@itemRou.get("/item", response_model=list[ItemOut])
async def get_items(
    zuid: UUID = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
):
    items = await fetch_items(zuid, db)
    return [_to_out(item) for item in items]


@itemRou.post("/item", response_model=ItemOut)
async def post_item(
    payload: ItemCreate,
    zuid: UUID = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
):
    item = await create_or_update_item(zuid, db, payload.model_dump(exclude_unset=True))
    return _to_out(item)
