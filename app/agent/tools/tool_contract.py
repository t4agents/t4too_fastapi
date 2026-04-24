from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AgentToolContract:
    name: str
    description: str
    input_schema: dict[str, Any]
    route: str
    notes: str = ""


def get_agent_tool_contracts() -> list[AgentToolContract]:
    """
    Internal tool registry for the router-based agent.

    This intentionally mirrors MCP tool metadata style:
    - name
    - description
    - input schema
    """
    return [
        AgentToolContract(
            name="rag_answer",
            description="Retrieve tenant-grounded context and answer with citations.",
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "integer", "minimum": 1, "maximum": 100},
                },
                "required": ["query"],
            },
            route="rag",
            notes="Maps to app.agent.tools.rag_tool.run_rag_rerank",
        ),
        AgentToolContract(
            name="run_sql_select",
            description="Run read-only SQL (single SELECT/CTE SELECT) on tenant data.",
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "sql": {"type": "string"},
                },
                "required": ["sql"],
            },
            route="sql",
            notes="Guarded by validate_sql_select before execute_sql",
        ),
        AgentToolContract(
            name="general_answer",
            description="Answer non-tenant general questions with a concise response.",
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "query": {"type": "string"},
                },
                "required": ["query"],
            },
            route="general",
            notes="Maps to app.agent.tools.general_tool.general_answer",
        ),
    ]


def get_mcp_like_tools() -> list[dict[str, Any]]:
    """
    Return MCP-compatible-ish tool descriptors for easy migration.

    If you later add a true MCP server, this metadata can be reused
    almost directly in the server's list-tools response.
    """
    return [
        {
            "name": c.name,
            "description": c.description,
            "inputSchema": c.input_schema,
            "x_route": c.route,
            "x_notes": c.notes,
        }
        for c in get_agent_tool_contracts()
    ]
