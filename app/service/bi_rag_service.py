from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repo.bi_rag_repo import bi_search_payroll_history_by_vector
from app.service.bi_rag_helper import bi_embed_query_text, bi_extract_cli_id, bi_vector_literal


async def bi_rag_query_service(
    query: str,
    top_k: int,
    zjwt: JWType,
    db: AsyncSession,
) -> dict:
    cli_id = bi_extract_cli_id(zjwt)
    query_vector = await bi_embed_query_text(query)
    query_vector_literal = bi_vector_literal(query_vector)

    rows = await bi_search_payroll_history_by_vector(
        db=db,
        cli_id=cli_id,
        query_vector_literal=query_vector_literal,
        top_k=top_k,
    )

    results: list[dict] = []
    for row in rows:
        distance = row.get("distance")
        score = None if distance is None else 1 - float(distance)
        results.append(
            {
                "embedding": row.get("embedding") or {},
                "history": row.get("history") or {},
                "distance": distance,
                "score": score,
            }
        )

    return {
        "query": query,
        "top_k": top_k,
        "results": results,
    }
