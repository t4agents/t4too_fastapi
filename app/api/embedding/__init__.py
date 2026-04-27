from fastapi import APIRouter

from .bi_rag import biRagRou

rouBI = APIRouter()
rouBI.include_router(biRagRou, tags=["bi-rag"])
