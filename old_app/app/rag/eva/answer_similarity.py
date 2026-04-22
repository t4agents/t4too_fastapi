import json
import logging
import math
from . import ragutils as ru

from fastapi import HTTPException
from sqlalchemy import select, text

from app.core.dependency_injection import ZMeDataClass
from app.db.db_async import T4DbSession
from app.db.models.ai_gold_dataset import RAGEvalDatasetDB, RAGEvalResultDB, RAGEvalRunDB
from app.db.models.m_payroll_history import PayrollHistory
from app.llm.conn.openai_embedder import EMBED_MODEL, embed_fn
from app.schemas.sch_ai_embedding import RagQueryRequest
from app.schemas.sch_ai_rag_answer_similarity import (
    RagEvalAnswerSimilarityRequest,
    RagEvalAnswerSimilarityResponse,
    RagEvalAnswerSimilarityRow,
)
from app.service.ser_ai_embedding import rag_answer_rerank

logger = logging.getLogger("app.http")


def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float | None:
    if not vec_a or not vec_b:
        return None
    if len(vec_a) != len(vec_b):
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


async def _get_context(session, source_id: str):
    logger.info("===similarity:context source_id=%s", str(source_id))
    result = await session.execute(
        select(PayrollHistory).where(PayrollHistory.id == source_id)
    )
    row = result.scalar_one_or_none()
    if not row:
        return None, None, None
    zuid = row.owner_id or row.created_by or row.employee_id
    logger.info("===similarity:context ok user_id=%s", str(zuid)[:5])
    return row.ten_id, row.biz_id, zuid


async def run_answer_similarity(
    payload: RagEvalAnswerSimilarityRequest,
) -> RagEvalAnswerSimilarityResponse:
    async with T4DbSession() as session:
        logger.info("===similarity:db_session_open")
        run = RAGEvalRunDB(
            embedding_version=f"{EMBED_MODEL}/384",
            model_version="rag-eval-answer-similarity",
            description=payload.description,
        )
        session.add(run)
        await session.flush()
        logger.info("===similarity:run_created run_id=%s", str(run.id)[:5])

        stmt = select(RAGEvalDatasetDB).where(RAGEvalDatasetDB.is_active.is_(True))
        if payload.category and payload.category.lower() != "rag":
            stmt = stmt.where(RAGEvalDatasetDB.category == payload.category)
        if payload.limit:
            stmt = stmt.limit(payload.limit)

        dataset_rows = (await session.execute(stmt)).scalars().all()
        logger.info("===similarity:dataset_loaded count=%s", len(dataset_rows))
        if not dataset_rows:
            raise HTTPException(status_code=404, detail="No active dataset rows found.")

        results: list[RAGEvalResultDB] = []
        rows: list[RagEvalAnswerSimilarityRow] = []
        current_ten_id = None
        similarity_values: list[float | None] = []

        for idx, row in enumerate(dataset_rows, start=1):
            logger.info("===similarity:row_start dataset_id=%s", str(row.id)[:5])
            relevant_ids = [str(x) for x in (row.relevant_source_ids or [])]
            if not relevant_ids:
                continue

            ten_id, biz_id, user_id = await _get_context(session, relevant_ids[0])
            if not ten_id or not biz_id or not user_id:
                continue

            if current_ten_id != ten_id:
                await session.execute(
                    text("select set_config('t4rls.tid', :ten_id, true)"),
                    {"ten_id": str(ten_id)},
                )
                current_ten_id = ten_id
                logger.info("===similarity:tenant_switch ten_id=%s", str(ten_id)[:5])

            zme = ZMeDataClass(ztid=ten_id, zbid=biz_id, zuid=user_id, zdb=session)

            rag_payload = RagQueryRequest(query=row.question, top_k=payload.top_k)
            logger.info("===similarity:rag_start")
            rag_response = await rag_answer_rerank(rag_payload, zme)
            answer_text = (rag_response or {}).get("answer") or ""

            answer_similarity, similarity_note = await _answer_similarity(
                answer_text,
                row.expected_answer or "",
            )

            results.append(
                RAGEvalResultDB(
                    dataset_id=row.id,
                    run_id=run.id,
                    retrieved_source_ids=[
                        str(e.get("source_id"))
                        for e in ((rag_response or {}).get("evidence") or [])
                        if e.get("source_id")
                    ],
                    answer=answer_text,
                    recall_at_k=None,
                    precision_at_k=None,
                    is_correct=None,
                    is_faithful=None,
                    eval_notes=json.dumps(
                        {
                            "metric": "answer_similarity",
                            "top_k": payload.top_k,
                            "similarity_note": similarity_note,
                        },
                        ensure_ascii=False,
                    ),
                )
            )

            row_out = RagEvalAnswerSimilarityRow(
                run_id=str(run.id),
                dataset_id=str(row.id),
                question=row.question,
                expected_answer=row.expected_answer or "",
                answer=answer_text,
                answer_similarity=answer_similarity,
                similarity_note=similarity_note,
                top_k=payload.top_k,
            )
            if payload.include_rows:
                rows.append(row_out)

            similarity_values.append(answer_similarity)
            logger.info(
                "===similarity:row_done idx=%s dataset_id=%s",
                idx,
                str(row.id),
            )

        if results:
            logger.info("===similarity:db_add_results count=%s", len(results))
            session.add_all(results)
        logger.info("===similarity:db_commit start")
        await session.commit()
        logger.info(
            "===similarity:committed run_id=%s results=%s",
            str(run.id),
            len(results),
        )

        avg_similarity = ru.avg(similarity_values)
        total = len(rows) if payload.include_rows else len(results)

        response = RagEvalAnswerSimilarityResponse(
            run_id=str(run.id),
            description=payload.description,
            top_k=payload.top_k,
            total=total,
            avg_answer_similarity=avg_similarity,
            rows=rows if payload.include_rows else None,
        )
        logger.info(
            "===similarity:done run_id=%s total=%s avg_similarity=%s",
            str(run.id),
            total,
            f"{avg_similarity:.4f}" if avg_similarity is not None else "None",
        )
        logger.info("===similarity:db_session_close")
        return response
