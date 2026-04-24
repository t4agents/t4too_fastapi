# Agent Folder Guide

## What This Folder Is Doing

Active flow in production:

1. `app/agent/executor/router_executor.py`
2. `app/agent/brain/router_brain.py`
3. `app/agent/tools/*`

The router picks one route:

- `rag`: tenant-grounded retrieval + rerank (`run_rag_rerank`)
- `sql`: guarded read-only SQL generation + execution
- `general`: direct general answer

## Is It Still Workable?

Yes. The active API path imports:

- `app/service/ser_ai_router.py` -> `app.agent.executor.router_executor.route_and_answer`

Legacy files currently present but not in the main API route:

- `app/agent/age_brain.py`
- `app/agent/age_executor.py`
- `app/agent/age_tools.py`
- `app/agent/ag1/*`

Those look like earlier experiments and may contain stale assumptions.

## MCP Comparison

This folder is not an MCP server yet, but it is close conceptually:

- Current `brain` router = tool selection logic.
- Current `tools` module = tool implementations.
- New `tool_contract.py` = MCP-like tool metadata (`name`, `description`, `inputSchema`).

If you want full MCP integration next, we can expose `get_mcp_like_tools()` and route calls through a true MCP server transport.
