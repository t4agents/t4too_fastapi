from __future__ import annotations

import time
from urllib.parse import urljoin

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings_singleton
from app.db.conn.db_async import get_db_admin

from ....db.models.acc.ac_mcp import get_recent_bank_transactions, get_vendor_by_name

router = APIRouter(prefix="/mcp_callback/acc", tags=["mcp-callback-acc"])
settings = get_settings_singleton()


class OCRRequest(BaseModel):
    text: str


@router.get("/health")
async def health(request: Request) -> dict[str, object]:
    # This endpoint verifies local service health and triggers agents->mcp diagnosis.
    local_url = str(request.url)
    caller_url = request.headers.get("origin") or request.headers.get("referer")
    service_name = request.url.hostname or "t4too_fastapi"
    agents_diagnose_url = urljoin(str(settings.TOO_AGENTS_API_URL), "diagnose_mcp")

    local_check = {
        "url": local_url,
        "base_url": str(request.base_url),
        "service": service_name,
        "status": "ok",
    }
    if caller_url:
        local_check["caller_url"] = caller_url

    agents_check: dict[str, object] = {
        "url": agents_diagnose_url,
        "status": "unknown",
    }

    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(agents_diagnose_url)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)

        agents_check["http_status"] = response.status_code
        agents_check["latency_ms"] = elapsed_ms
        agents_check["status"] = "ok" if response.is_success else "failed"
        try:
            agents_check["response"] = response.json()
        except ValueError:
            agents_check["response"] = response.text
    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        agents_check["status"] = "failed"
        agents_check["latency_ms"] = elapsed_ms
        agents_check["error"] = str(exc)

    overall_status = "ok" if agents_check["status"] == "ok" else "degraded"
    return {
        "status": overall_status,
        "checks": {
            "current_repo": local_check,
            "agents_and_mcp": agents_check,
        },
    }


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
