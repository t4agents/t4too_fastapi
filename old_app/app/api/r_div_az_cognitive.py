# app/api/routes/reports.py
import os, secrets
from fastapi import APIRouter, Depends, UploadFile, File, Query
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.db_async import get_db
from app.service.ser_div_az_search import search_dividends
from app.service.ser_div_chunk import DividendChunkService
from app.service.ser_div_embedding import EmbeddingService
from app.service.ser_div_pgvector2azure import bulk_index_dividends

security = HTTPBasic()

def require_password(credentials: HTTPBasicCredentials = Depends(security),):
    correct_pass = secrets.compare_digest(credentials.password,os.environ["ADMIN_PASSWORD"],)
    if not correct_pass:return


AdminDeps = Depends(require_password)

congnitiveRou = APIRouter()

@congnitiveRou.get("/cognitive-search", dependencies=[AdminDeps])
async def search(q: str, top_k: int = 10):
    return await search_dividends(q, top_k)



@congnitiveRou.post("/az-cognitive-search-index", dependencies=[AdminDeps])
async def reindex(db: AsyncSession = Depends(get_db),):
    await bulk_index_dividends(db)