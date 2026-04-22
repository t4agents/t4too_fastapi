from typing import Optional
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class GuardrailQueryRequest(BaseModel):
    start_ts: Optional[datetime] = None
    end_ts: Optional[datetime] = None
    route: Optional[str] = None
    model: Optional[str] = None
    ten_id: Optional[UUID] = None
    biz_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    max_rows: int = Field(default=5000, ge=1)


class GuardrailRateResponse(BaseModel):
    total: int
    flagged: int
    rate: Optional[float] = None


class GuardrailLatencyResponse(BaseModel):
    total: int
    avg_ms: Optional[float] = None
    p50_ms: Optional[float] = None
    p90_ms: Optional[float] = None
    p95_ms: Optional[float] = None
    p99_ms: Optional[float] = None
    min_ms: Optional[float] = None
    max_ms: Optional[float] = None


class GuardrailCostResponse(BaseModel):
    total: int
    total_usd: Optional[float] = None
    avg_usd: Optional[float] = None
    p50_usd: Optional[float] = None
    p90_usd: Optional[float] = None
    p95_usd: Optional[float] = None
    p99_usd: Optional[float] = None
    min_usd: Optional[float] = None
    max_usd: Optional[float] = None
