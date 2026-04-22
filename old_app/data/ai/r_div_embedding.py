# app/api/routes/reports.py
import os, secrets
from fastapi import APIRouter, Depends, UploadFile, File, Query
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.db_async import get_session
from app.service.ser_div_az_search import search_dividends
from app.service.ser_div_chunk import DividendChunkService
from app.service.ser_div_embedding import EmbeddingService
from app.service.ser_div_pgvector2azure import bulk_index_dividends

security = HTTPBasic()

def require_password(credentials: HTTPBasicCredentials = Depends(security),):
    correct_pass = secrets.compare_digest(credentials.password,os.environ["ADMIN_PASSWORD"],)
    if not correct_pass:return


AdminDeps = Depends(require_password)

divEmbedding = APIRouter()


@divEmbedding.post("/rebuild-chunks", summary="Rebuild dividend_chunks from dividends",)
async def rebuild_dividend_chunks(
    db: AsyncSession = Depends(get_session),
):
    service = DividendChunkService(db)
    return await service.rebuild_chunks()


@divEmbedding.post("/embed-all")
async def embed_all_div(db: AsyncSession = Depends(get_session),):
    count = await EmbeddingService.embed_all_dummy(db)
    return {"embedded": count}



# @divEmbedding.post("/admin/reindex", dependencies=[AdminDeps])
# async def reindex(db: AsyncSession = Depends(get_db),):
#     await bulk_index_dividends(db)