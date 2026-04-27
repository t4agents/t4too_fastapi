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

from .ser_div_chunk import InvChunkService
from .ser_div_embedding import EmbeddingService


invEmbedding = APIRouter()


@invEmbedding.post("/rebuild-chunks", summary="Rebuild dividend_chunks from dividends",)
async def rebuild_inv_chunks(
    db: AsyncSession = Depends(get_db_rls),
):
    service = InvChunkService(db)
    return await service.rebuild_chunks()


@invEmbedding.post("/embed-all")
async def embed_all_inv(db: AsyncSession = Depends(get_db_rls),):
    count = await EmbeddingService.embed_all_dummy(db)
    return {"embedded": count}



# @invEmbedding.post("/admin/reindex", dependencies=[AdminDeps])
# async def reindex(db: AsyncSession = Depends(get_db_rls),):
#     await bulk_index_dividends(db)