from __future__ import annotations

import json

from fastapi import HTTPException
from sqlalchemy import select

from app.db.models.ai.ai_gold_dataset import RAGEvalDatasetDB, RAGEvalResultDB, RAGEvalRunDB
from app.llm.conn.openai_embedder import EMBED_MODEL
from app.schemas.sch_ai_embedding import RagQueryRequest
from app.schemas.sch_ai_rag_recall import RagEvalRecallRequest, RagEvalRecallResponse, RagEvalRecallRow
from app.service.ser_ai_context import AIContext
from app.service.ser_ai_embedding import rag_answer_rerank


def _avg(values: list[float | None]) -> float | None:
    nums = [v for v in values if isinstance(v, (int, float))]
    if not nums:
        return None
    return sum(nums) / len(nums)


async def run_recall_at_k(payload: RagEvalRecallRequest, ctx: AIContext) -> RagEvalRecallResponse:
    run = RAGEvalRunDB(
        embedding_version=f"{EMBED_MODEL}/384",
        model_version="rag-eval-recall",
        description=payload.description,
    )
    ctx.db.add(run)
    await ctx.db.flush()

    stmt = select(RAGEvalDatasetDB).where(RAGEvalDatasetDB.is_active.is_(True))
    if payload.category and payload.category.lower() != "rag":
        stmt = stmt.where(RAGEvalDatasetDB.category == payload.category)
    if payload.limit:
        stmt = stmt.limit(payload.limit)
    dataset_rows = (await ctx.db.execute(stmt)).scalars().all()
    if not dataset_rows:
        raise HTTPException(status_code=404, detail="No active dataset rows found.")

    results: list[RAGEvalResultDB] = []
    rows: list[RagEvalRecallRow] = []
    recall_values: list[float | None] = []

    for row in dataset_rows:
        relevant_ids = [str(x) for x in (row.relevant_source_ids or [])]
        if not relevant_ids:
            continue

        rag_payload = RagQueryRequest(query=row.question, top_k=payload.top_k)
        rag_response = await rag_answer_rerank(rag_payload, ctx)
        evidence = (rag_response or {}).get("evidence") or []
        retrieved_ids = [str(e.get("source_id")) for e in evidence if e.get("source_id")]

        relevant_set = set(relevant_ids)
        retrieved_set = set(retrieved_ids)
        hit_count = len(relevant_set & retrieved_set)
        recall_at_k = hit_count / len(relevant_set) if relevant_set else (1.0 if not retrieved_set else 0.0)

        results.append(
            RAGEvalResultDB(
                dataset_id=row.id,
                run_id=run.id,
                retrieved_source_ids=retrieved_ids,
                answer=(rag_response or {}).get("answer") or "",
                recall_at_k=recall_at_k,
                precision_at_k=None,
                is_correct=None,
                is_faithful=None,
                eval_notes=json.dumps({"metric": "recall_at_k", "top_k": payload.top_k}, ensure_ascii=False),
            )
        )
        if payload.include_rows:
            rows.append(
                RagEvalRecallRow(
                    run_id=str(run.id),
                    dataset_id=str(row.id),
                    question=row.question,
                    expected_source_ids=relevant_ids,
                    retrieved_source_ids=retrieved_ids,
                    recall_at_k=recall_at_k,
                    top_k=payload.top_k,
                )
            )
        recall_values.append(recall_at_k)

    if results:
        ctx.db.add_all(results)
    await ctx.db.flush()

    total = len(rows) if payload.include_rows else len(results)
    return RagEvalRecallResponse(
        run_id=str(run.id),
        description=payload.description,
        top_k=payload.top_k,
        total=total,
        avg_recall_at_k=_avg(recall_values),
        rows=rows if payload.include_rows else None,
    )
