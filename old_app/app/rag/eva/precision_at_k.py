import json
import logging
from . import ragutils as ru

from fastapi import HTTPException
from sqlalchemy import select, text

from app.core.dependency_injection import ZMeDataClass
from app.db.db_async import T4DbSession
from app.db.models.ai_gold_dataset import RAGEvalDatasetDB, RAGEvalResultDB, RAGEvalRunDB
from app.db.models.m_payroll_history import PayrollHistory
from app.llm.conn.openai_embedder import EMBED_MODEL
from app.schemas.sch_ai_embedding import RagQueryRequest
from app.schemas.sch_ai_rag_precision import (
    RagEvalPrecisionRequest,
    RagEvalPrecisionResponse,
    RagEvalPrecisionRow,
)
from app.service.ser_ai_embedding import rag_answer_rerank

logger = logging.getLogger("app.http")


async def _get_context(session, source_id: str):
    logger.info("===precision:get_context source_id=%s", str(source_id))
    result = await session.execute(
        select(PayrollHistory).where(PayrollHistory.id == source_id)
    )
    row = result.scalar_one_or_none()
    if not row:
        return None, None, None
    zuid = row.owner_id or row.created_by or row.employee_id
    logger.info("===precision:get_context ok user_id=%s", str(zuid)[:5])
    return row.ten_id, row.biz_id, zuid


async def run_precision_at_k(payload: RagEvalPrecisionRequest) -> RagEvalPrecisionResponse:
    async with T4DbSession() as session:
        logger.info("===precision:db_session_open")
        run = RAGEvalRunDB(
            embedding_version=f"{EMBED_MODEL}/384",
            model_version="rag-eval-precision",
            description=payload.description,
        )
        session.add(run)
        await session.flush()
        logger.info("===precision:run_created run_id=%s", str(run.id)[:5])

        stmt = select(RAGEvalDatasetDB).where(RAGEvalDatasetDB.is_active.is_(True))
        if payload.category and payload.category.lower() != "rag":
            stmt = stmt.where(RAGEvalDatasetDB.category == payload.category)
        if payload.limit:
            stmt = stmt.limit(payload.limit)

        dataset_rows = (await session.execute(stmt)).scalars().all()
        logger.info("===precision:dataset_loaded count=%s", len(dataset_rows))
        if not dataset_rows:
            raise HTTPException(status_code=404, detail="No active dataset rows found.")

        results: list[RAGEvalResultDB] = []
        rows: list[RagEvalPrecisionRow] = []
        current_ten_id = None
        precision_values: list[float | None] = []

        for idx, row in enumerate(dataset_rows, start=1):
            logger.info("===precision:row_start dataset_id=%s", str(row.id)[:5])
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
                logger.info("===precision:tenant_switch ten_id=%s", str(ten_id)[:5])

            zme = ZMeDataClass(ztid=ten_id, zbid=biz_id, zuid=user_id, zdb=session)

            rag_payload = RagQueryRequest(query=row.question, top_k=payload.top_k)
            logger.info("===precision:embedding_start")
            rag_response = await rag_answer_rerank(rag_payload, zme)
            evidence = (rag_response or {}).get("evidence") or []
            retrieved_ids = [str(e.get("source_id")) for e in evidence if e.get("source_id")]

            relevant_set = set(relevant_ids)
            retrieved_set = set(retrieved_ids)

            hit_count = len(relevant_set & retrieved_set)
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
                    eval_notes=json.dumps(
                        {"metric": "precision_at_k", "top_k": payload.top_k},
                        ensure_ascii=False,
                    ),
                )
            )

            row_out = RagEvalPrecisionRow(
                run_id=str(run.id),
                dataset_id=str(row.id),
                question=row.question,
                expected_source_ids=relevant_ids,
                retrieved_source_ids=retrieved_ids,
                precision_at_k=precision_at_k,
                top_k=payload.top_k,
            )
            if payload.include_rows:
                rows.append(row_out)

            precision_values.append(precision_at_k)
            logger.info(
                "===precision:row_done idx=%s dataset_id=%s",
                idx,
                str(row.id),
            )

        if results:
            logger.info("===precision:db_add_results count=%s", len(results))
            session.add_all(results)
        logger.info("===precision:db_commit start")
        await session.commit()
        logger.info(
            "===precision:committed run_id=%s results=%s",
            str(run.id),
            len(results),
        )

        avg_precision = ru.avg(precision_values)
        total = len(rows) if payload.include_rows else len(results)

        response = RagEvalPrecisionResponse(
            run_id=str(run.id),
            description=payload.description,
            top_k=payload.top_k,
            total=total,
            avg_precision_at_k=avg_precision,
            rows=rows if payload.include_rows else None,
        )
        logger.info(
            "===precision:done run_id=%s total=%s avg_precision=%s",
            str(run.id),
            total,
            f"{avg_precision:.4f}" if avg_precision is not None else "None",
        )
        logger.info("===precision:db_session_close")
        return response
