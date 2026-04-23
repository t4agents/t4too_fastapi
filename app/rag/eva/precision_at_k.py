from __future__ import annotations
from app.schemas.sch_ai import JWType

import json

from fastapi import HTTPException
from sqlalchemy import select

from app.db.models.ai.ai_gold_dataset import RAGEvalDatasetDB, RAGEvalResultDB, RAGEvalRunDB
from app.llm.conn.openai_embedder import EMBED_MODEL
from app.schemas.sch_ai_rag_basic import QueryReq
from app.schemas.sch_ai_rag_precision import (
    RagEvalPrecisionRequest,
    RagEvalPrecisionResponse,
    RagEvalPrecisionRow,
)

# from app.service.ser_ai_embedding import rag_answer_rerank


def _avg(values: list[float | None]) -> float | None:
    nums = [v for v in values if isinstance(v, (int, float))]
    if not nums:
        return None
    return sum(nums) / len(nums)


async def run_precision_at_k(payload: RagEvalPrecisionRequest, zjwt: JWType) -> RagEvalPrecisionResponse:
    run = RAGEvalRunDB(
        embedding_version=f"{EMBED_MODEL}/384",
        model_version="rag-eval-precision",
        description=payload.description,
    )
    add(run)
    await flush()

    stmt = select(RAGEvalDatasetDB).where(RAGEvalDatasetDB.is_active.is_(True))
    if payload.category and payload.category.lower() != "rag":
        stmt = stmt.where(RAGEvalDatasetDB.category == payload.category)
    if payload.limit:
        stmt = stmt.limit(payload.limit)
    dataset_rows = (await db.execute(stmt)).scalars().all()
    if not dataset_rows:
        raise HTTPException(status_code=404, detail="No active dataset rows found.")

    results: list[RAGEvalResultDB] = []
    rows: list[RagEvalPrecisionRow] = []
    precision_values: list[float | None] = []

    for row in dataset_rows:
        relevant_ids = [str(x) for x in (row.relevant_source_ids or [])]
        if not relevant_ids:
            continue

        rag_payload = QueryReq(query=row.question, top_k=payload.top_k)
        rag_response = await rag_answer_rerank(rag_payload, ctx)
        evidence = (rag_response or {}).get("evidence") or []
        retrieved_ids = [str(e.get("source_id")) for e in evidence if e.get("source_id")]

        hit_count = len(set(relevant_ids) & set(retrieved_ids))
        precision_at_k = hit_count / max(payload.top_k, 1)

        results.append(
            RAGEvalResultDB(
                dataset_id=row.id,
                run_id=run.id,
                retrieved_source_ids=retrieved_ids,
                answer=(rag_response or {}).get("answer") or "",
                recall_at_k=None,
                precision_at_k=precision_at_k,
                is_correct=None,
                is_faithful=None,
                eval_notes=json.dumps({"metric": "precision_at_k", "top_k": payload.top_k}, ensure_ascii=False),
            )
        )
        if payload.include_rows:
            rows.append(
                RagEvalPrecisionRow(
                    run_id=str(run.id),
                    dataset_id=str(row.id),
                    question=row.question,
                    expected_source_ids=relevant_ids,
                    retrieved_source_ids=retrieved_ids,
                    precision_at_k=precision_at_k,
                    top_k=payload.top_k,
                )
            )
        precision_values.append(precision_at_k)

    if results:
        add_all(results)
    await flush()

    total = len(rows) if payload.include_rows else len(results)
    return RagEvalPrecisionResponse(
        run_id=str(run.id),
        description=payload.description,
        top_k=payload.top_k,
        total=total,
        avg_precision_at_k=_avg(precision_values),
        rows=rows if payload.include_rows else None,
    )
