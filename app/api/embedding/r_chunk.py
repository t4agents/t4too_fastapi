# app/api/routes/reports.py
import os, secrets
from fastapi import APIRouter, Depends, UploadFile, File, Query
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.auth import get_zjwt
from app.db.conn.db_rls import get_db_rls
from app.schemas.sch_ai import JWType
from app.schemas.sch_ai_rag_basic import QueryReq, QueryRes
from app.service.bi_rag_service import bi_rag_query_service

from .ser_chunk import InvChunkService


invChunk = APIRouter()


@invChunk.post("/rebuild-inv-chunks", summary="delete all embeddings in inv_1024 and re-chunk",)
async def rebuild_inv_chunks(
    zjwt: JWType = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
):
    service = InvChunkService(db)
    return await service.rebuild_chunks(zjwt)
