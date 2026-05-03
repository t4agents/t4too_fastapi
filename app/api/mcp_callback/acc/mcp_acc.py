from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.conn.db_async import get_db_admin

from ....db.models.acc.ac_mcp import get_recent_bank_transactions, get_vendor_by_name

router = APIRouter(prefix="/mcp_callback/acc", tags=["mcp-callback-acc"])


class OCRRequest(BaseModel):
    text: str


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/vendors/lookup")
async def lookup_vendor(
    name: str,
    db: AsyncSession = Depends(get_db_admin),
) -> dict[str, str]:
    row = await get_vendor_by_name(db, name)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Vendor '{name}' not found")

    return {
        "name": row.name,
        "category": row.category,
        "risk_level": row.risk_level,
        "status": row.status,
    }


@router.get("/bank/query")
async def query_bank(
    account_name: str,
    db: AsyncSession = Depends(get_db_admin),
) -> dict[str, object]:
    rows = await get_recent_bank_transactions(db, account_name=account_name, limit=5)
    items = [
        {
            "account_name": row.account_name,
            "description": row.description,
            "amount": float(row.amount),
            "currency": row.currency,
            "posted_at": row.posted_at.isoformat(),
        }
        for row in rows
    ]
    balance_hint = sum(item["amount"] for item in items)
    return {
        "account_name": account_name,
        "recent_transactions": items,
        "recent_net_change": balance_hint,
    }


@router.post("/ocr/extract")
def ocr_extract(payload: OCRRequest) -> dict[str, object]:
    words = payload.text.strip().split()
    return {
        "raw_text": payload.text,
        "word_count": len(words),
        "uppercase_preview": payload.text.upper()[:80],
    }
