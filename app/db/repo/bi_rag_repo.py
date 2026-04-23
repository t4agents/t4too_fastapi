from __future__ import annotations

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def bi_search_payroll_history_by_vector(
    db: AsyncSession,
    cli_id: UUID,
    query_vector_literal: str,
    top_k: int,
) -> list[dict]:
    stmt = text(
        """
        SELECT
            to_jsonb(e) AS embedding,
            to_jsonb(h) AS history,
            (
                e.emb384 OPERATOR(extensions.<=>)
                CAST(:query_vector AS extensions.vector(384))
            )::float8 AS distance
        FROM too_ai.payroll_history_384 e
        JOIN too_t4.payroll_history h
          ON h.id = e.source_id
        WHERE h.cli_id = :cli_id
        ORDER BY distance ASC
        LIMIT :top_k
        """
    )
    result = await db.execute(
        stmt,
        {
            "query_vector": query_vector_literal,
            "cli_id": cli_id,
            "top_k": top_k,
        },
    )
    return [dict(row) for row in result.mappings().all()]
