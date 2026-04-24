from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from fastapi import Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.sch_ai import JWType
from app.schemas.sch_ai_router import RouterQueryRequest

LanggraphRouteFn = Callable[..., Awaitable[Any]]


def _format_sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _format_sse_comment(comment: str) -> str:
    return f": {comment}\n\n"


def build_langgraph_sse_response(
    payload: RouterQueryRequest,
    request: Request,
    zjwt: JWType,
    db: AsyncSession,
    route_langgraph: LanggraphRouteFn,
    logger: logging.Logger,
) -> StreamingResponse:
    
    # 1. 创建异步队列 (数据管道), 作为 runner 和 event_stream 之间的通信桥梁. runner 生产数据，event_stream 消费数据
    queue: asyncio.Queue[tuple[str, dict[str, Any]] | None] = asyncio.Queue()
    keepalive_seconds = 15.0

    # 2. 定义回调函数 (接入业务逻辑), 将 LangGraph 的执行状态推入队列 使业务代码能无感知地输出 SSE
    async def status_cb(status: str, meta: dict[str, Any] | None = None) -> None:
        await queue.put(("status", {"status": status, "meta": meta or {}}))

    # 3. Runner 生产数据 (执行业务逻辑) 执行真实业务逻辑， 通过回调或直接 put 将中间结果和最终结果送入队列
    async def runner() -> None:
        try:
            result = await route_langgraph(payload, zjwt, db, status_cb=status_cb)
            await queue.put(("final", {"response": result}))
        except Exception as exc:
            logger.exception("lgstream failed", exc_info=exc)
            await queue.put(("error", {"message": "internal_error"}))
        finally:
            await queue.put(None)

    # 4. Event Stream 消费并格式化 (核心 SSE 生成)
    async def event_stream():
        # Emit a first chunk immediately to avoid proxy/client buffering.
        yield _format_sse("status", {"status": "start", "meta": {"query": payload.query, "top_k": payload.top_k}})
        task = asyncio.create_task(runner())
        try:
            while True:
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=keepalive_seconds)
                except asyncio.TimeoutError:
                    yield _format_sse_comment(f"keepalive {datetime.now(timezone.utc).isoformat()}")
                    if await request.is_disconnected():
                        task.cancel()
                        break
                    continue

                if item is None: break

                event, data = item
                yield _format_sse(event, data)
                if await request.is_disconnected():
                    task.cancel()
                    break
        except asyncio.CancelledError:
            task.cancel()
            raise

    headers = {
        "Cache-Control": "no-cache, no-transform",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    
    # 最关键的 3 个要素：✅ media_type="text/event-stream"✅ yield 多次返回数据（不是 return）✅ 禁用缓冲的 headers（Cache-Control, X-Accel-Buffering）
    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=headers)
