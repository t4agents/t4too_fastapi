from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class FeedbackCreateRequest(BaseModel):
    feedback_type: str = Field(..., min_length=1)
    rating: Optional[int] = Field(default=None, ge=-1, le=1)
    reason: Optional[str] = None
    comment: Optional[str] = None
    route: Optional[str] = None
    model: Optional[str] = None
    session_id: Optional[str] = None
    message_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    meta: Optional[Dict[str, Any]] = None


class FeedbackCreateResponse(BaseModel):
    status: str = "ok"
