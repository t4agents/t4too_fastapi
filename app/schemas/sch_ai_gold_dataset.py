from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class GoldDatasetCreateRequest(BaseModel):
    question: str = Field(..., min_length=1)
    expected_answer: str = Field(..., min_length=1)
    relevant_source_ids: list[str] = Field(default_factory=list)
    category: Optional[str] = "rag"
    difficulty: Optional[int] = Field(default=None, ge=1, le=5)
    is_active: bool = True


class GoldDatasetUpdateRequest(BaseModel):
    id: str
    question: Optional[str] = None
    expected_answer: Optional[str] = None
    relevant_source_ids: Optional[list[str]] = None
    category: Optional[str] = None
    difficulty: Optional[int] = Field(default=None, ge=1, le=5)
    is_active: Optional[bool] = None


class GoldDatasetOut(BaseModel):
    id: str
    question: str
    expected_answer: str
    relevant_source_ids: list[str]
    category: Optional[str] = None
    difficulty: Optional[int] = None
    is_active: bool
