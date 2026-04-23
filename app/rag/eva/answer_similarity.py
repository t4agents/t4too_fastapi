from __future__ import annotations

import json
import math

from fastapi import HTTPException
from sqlalchemy import select

from app.db.models.ai.ai_gold_dataset import RAGEvalDatasetDB, RAGEvalResultDB, RAGEvalRunDB
from app.llm.conn.openai_embedder import EMBED_MODEL, embed_fn
from app.schemas.sch_ai import JWType
from app.schemas.sch_ai_rag_basic import QueryReq
from app.schemas.sch_ai_rag_answer_similarity import (
    RagEvalAnswerSimilarityRequest,
    RagEvalAnswerSimilarityResponse,
    RagEvalAnswerSimilarityRow,
)

# from app.service.ser_ai_embedding import rag_answer_rerank


def _avg(values: list[float | None]) -> float | None:
    nums = [v for v in values if isinstance(v, (int, float))]
    if not nums:
        return None
    return sum(nums) / len(nums)


def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float | None:
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return None
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for a, b in zip(vec_a, vec_b):
        dot += a * b
        norm_a += a * a
        norm_b += b * b
    if norm_a == 0.0 or norm_b == 0.0:
        return None
    return dot / math.sqrt(norm_a * norm_b)


async def _answer_similarity(answer: str, expected: str) -> tuple[float | None, str]:
    if not answer or not expected:
        return None, "missing_answer_or_expected"
    try:
        vec_answer = await embed_fn(answer)
        vec_expected = await embed_fn(expected)
        score = _cosine_similarity(vec_answer, vec_expected)
        return score, "ok" if score is not None else "invalid_vectors"
    except Exception as exc:
        return None, f"embed_error:{str(exc)}"


async def run_answer_similarity(payload: RagEvalAnswerSimilarityRequest, zjwt: JWType) -> RagEvalAnswerSimilarityResponse:
    run = RAGEvalRunDB(
        embedding_version=f"{EMBED_MODEL}/384",
        model_version="rag-eval-answer-similarity",
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
    rows: list[RagEvalAnswerSimilarityRow] = []
    similarity_values: list[float | None] = []

    for row in dataset_rows:
        rag_payload = QueryReq(query=row.question, top_k=payload.top_k)
        rag_response = await rag_answer_rerank(rag_payload, ctx)
        answer_text = (rag_response or {}).get("answer") or ""
        answer_similarity, similarity_note = await _answer_similarity(answer_text, row.expected_answer or "")

        results.append(
            RAGEvalResultDB(
                dataset_id=row.id,
                run_id=run.id,
                retrieved_source_ids=[str(e.get("source_id")) for e in ((rag_response or {}).get("evidence") or []) if e.get("source_id")],
                answer=answer_text,
                recall_at_k=None,
                precision_at_k=None,
                is_correct=None,
                is_faithful=None,
                eval_notes=json.dumps(
                    {"metric": "answer_similarity", "top_k": payload.top_k, "similarity_note": similarity_note},
                    ensure_ascii=False,
                ),
            )
        )
        if payload.include_rows:
            rows.append(
                RagEvalAnswerSimilarityRow(
                    run_id=str(run.id),
                    dataset_id=str(row.id),
                    question=row.question,
                    expected_answer=row.expected_answer or "",
                    answer=answer_text,
                    answer_similarity=answer_similarity,
                    similarity_note=similarity_note,
                    top_k=payload.top_k,
                )
            )
        similarity_values.append(answer_similarity)

    if results:
        add_all(results)
    await flush()

    total = len(rows) if payload.include_rows else len(results)
    return RagEvalAnswerSimilarityResponse(
        run_id=str(run.id),
        description=payload.description,
        top_k=payload.top_k,
        total=total,
        avg_answer_similarity=_avg(similarity_values),
        rows=rows if payload.include_rows else None,
    )
