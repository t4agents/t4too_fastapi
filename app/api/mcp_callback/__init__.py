from fastapi import APIRouter

from .acc import router as mcp_acc_router

rouMcpCallback = APIRouter()
rouMcpCallback.include_router(mcp_acc_router)
