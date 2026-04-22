import json
import logging
from . import ragutils as ru

from fastapi import HTTPException
from sqlalchemy import select, text

from app.agent.brain.llm_client import oai_client
from app.core.dependency_injection import ZMeDataClass
from app.db.db_async import T4DbSession
from app.db.models.ai_gold_dataset import RAGEvalDatasetDB, RAGEvalResultDB, RAGEvalRunDB
from app.db.models.m_payroll_history import PayrollHistory
from app.llm.conn.openai_embedder import EMBED_MODEL
from app.schemas.sch_ai_embedding import RagQueryRequest
from app.schemas.sch_ai_rag_answer_relevance import (
    RagEvalAnswerRelevanceRequest,
    RagEvalAnswerRelevanceResponse,
    RagEvalAnswerRelevanceRow,
)
from app.service.ser_ai_embedding import rag_answer_rerank
from openai.types.responses.response_format_text_json_schema_config_param import (
    ResponseFormatTextJSONSchemaConfigParam,
)
from openai.types.responses.response_text_config_param import ResponseTextConfigParam

logger = logging.getLogger("app.http")

JUDGE_MODEL = "gpt-5-mini"

RELEVANCE_FORMAT: ResponseFormatTextJSONSchemaConfigParam = {
    "type": "json_schema",
    "name": "answer_relevance_judgement",
    "description": "Judge if the answer is relevant and addresses the question and expected answer.",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "is_relevant": {"type": "boolean"},
            "rationale": {"type": "string"},
        },
        "required": ["is_relevant", "rationale"],
    },
    "strict": True,
}


async def _get_context(session, source_id: str):
    logger.info("===relevance:context source_id=%s", str(source_id))
    result = await session.execute(
        select(PayrollHistory).where(PayrollHistory.id == source_id)
    )
    row = result.scalar_one_or_none()
    if not row:
        return None, None, None
    zuid = row.owner_id or row.created_by or row.employee_id
    logger.info("===relevance:context ok user_id=%s", str(zuid)[:5])
    return row.ten_id, row.biz_id, zuid


async def _judge_relevance(
    question: str,
    answer: str,
    expected: str,
) -> tuple[bool | None, str]:
    if not answer or not expected or not question:
        return None, "missing_question_answer_or_expected"

    system_msg = (
        "You are a strict evaluator. Determine whether the answer is relevant and directly "
        "addresses the question and expected answer. If it is off-topic, incomplete, or mismatched, "
        "mark is_relevant=false. Return JSON only."
    )
    user_payload = {
        "question": question,
        "expected_answer": expected,
        "answer": answer,
    }

    text_config: ResponseTextConfigParam = {"format": RELEVANCE_FORMAT, "verbosity": "low"}

    response = await oai_client.responses.create(
        model=JUDGE_MODEL,
        input=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": json.dumps(user_payload)},
        ],
        text=text_config,
        reasoning={"summary": "auto"},
    )

    raw_text = response.output_text or ""
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        return None, "Judge output not valid JSON."

    is_relevant = payload.get("is_relevant")
    rationale = payload.get("rationale")
    if not isinstance(is_relevant, bool):
        is_relevant = None
    if not isinstance(rationale, str):
        rationale = ""

    return is_relevant, rationale


async def run_answer_relevance(
    payload: RagEvalAnswerRelevanceRequest,
) -> RagEvalAnswerRelevanceResponse:
    async with T4DbSession() as session:
        logger.info("===relevance:db_session_open")
        run = RAGEvalRunDB(
            embedding_version=f"{EMBED_MODEL}/384",
            model_version="rag-eval-answer-relevance",
            description=payload.description,
        )
        session.add(run)
        await session.flush()
        logger.info("===relevance:run_created run_id=%s", str(run.id)[:5])

        stmt = select(RAGEvalDatasetDB).where(RAGEvalDatasetDB.is_active.is_(True))
        if payload.category and payload.category.lower() != "rag":
            stmt = stmt.where(RAGEvalDatasetDB.category == payload.category)
        if payload.limit:
            stmt = stmt.limit(payload.limit)

        dataset_rows = (await session.execute(stmt)).scalars().all()
        logger.info("===relevance:dataset_loaded count=%s", len(dataset_rows))
        if not dataset_rows:
            raise HTTPException(status_code=404, detail="No active dataset rows found.")

        results: list[RAGEvalResultDB] = []
        rows: list[RagEvalAnswerRelevanceRow] = []
        current_ten_id = None
        relevance_values: list[float | None] = []

        for idx, row in enumerate(dataset_rows, start=1):
            logger.info("===relevance:row_start dataset_id=%s", str(row.id)[:5])
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
                logger.info("===relevance:tenant_switch ten_id=%s", str(ten_id)[:5])

            zme = ZMeDataClass(ztid=ten_id, zbid=biz_id, zuid=user_id, zdb=session)

            rag_payload = RagQueryRequest(query=row.question, top_k=payload.top_k)
            logger.info("===relevance:rag_start")
            rag_response = await rag_answer_rerank(rag_payload, zme)
            answer_text = (rag_response or {}).get("answer") or ""

            is_relevant, relevance_note = await _judge_relevance(
                row.question,
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
                            "metric": "answer_relevance",
                            "top_k": payload.top_k,
                            "relevance_note": relevance_note,
                            "judge": "llm",
                        },
                        ensure_ascii=False,
                    ),
                )
            )

            row_out = RagEvalAnswerRelevanceRow(
                run_id=str(run.id),
                dataset_id=str(row.id),
                question=row.question,
                expected_answer=row.expected_answer or "",
                answer=answer_text,
                is_relevant=is_relevant,
                relevance_note=relevance_note,
                top_k=payload.top_k,
            )
            if payload.include_rows:
                rows.append(row_out)

            relevance_values.append(
                1.0 if is_relevant is True else (0.0 if is_relevant is False else None)
            )
            logger.info(
                "===relevance:row_done idx=%s dataset_id=%s",
                idx,
                str(row.id),
            )

        if results:
            logger.info("===relevance:db_add_results count=%s", len(results))
            session.add_all(results)
        logger.info("===relevance:db_commit start")
        await session.commit()
        logger.info(
            "===relevance:committed run_id=%s results=%s",
            str(run.id),
            len(results),
        )

        avg_relevance = ru.avg(relevance_values)
        total = len(rows) if payload.include_rows else len(results)

        response = RagEvalAnswerRelevanceResponse(
            run_id=str(run.id),
            description=payload.description,
            top_k=payload.top_k,
            total=total,
            avg_answer_relevance=avg_relevance,
            rows=rows if payload.include_rows else None,
        )
        logger.info(
            "===relevance:done run_id=%s total=%s avg_relevance=%s",
            str(run.id),
            total,
            f"{avg_relevance:.4f}" if avg_relevance is not None else "None",
        )
        logger.info("===relevance:db_session_close")
        return response
