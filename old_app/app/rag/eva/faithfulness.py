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
from app.schemas.sch_ai_rag_faithfulness import (
    RagEvalFaithfulnessRequest,
    RagEvalFaithfulnessResponse,
    RagEvalFaithfulnessRow,
)
from app.service.ser_ai_embedding import rag_answer_rerank
from app.service.ser_ai_embedding import minimize_evidence_for_llm
from openai.types.responses.response_format_text_json_schema_config_param import (
    ResponseFormatTextJSONSchemaConfigParam,
)
from openai.types.responses.response_text_config_param import ResponseTextConfigParam

logger = logging.getLogger("app.http")

JUDGE_MODEL = "gpt-5-mini"

FAITHFULNESS_FORMAT: ResponseFormatTextJSONSchemaConfigParam = {
    "type": "json_schema",
    "name": "faithfulness_judgement",
    "description": "Judge whether the answer is fully supported by the evidence.",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "is_faithful": {"type": "boolean"},
            "rationale": {"type": "string"},
        },
        "required": ["is_faithful", "rationale"],
    },
    "strict": True,
}


async def _get_context(session, source_id: str):
    logger.info("===faith:context source_id=%s", str(source_id))
    result = await session.execute(
        select(PayrollHistory).where(PayrollHistory.id == source_id)
    )
    row = result.scalar_one_or_none()
    if not row:
        return None, None, None
    zuid = row.owner_id or row.created_by or row.employee_id
    logger.info("===faith:context ok user_id=%s", str(zuid)[:5])
    return row.ten_id, row.biz_id, zuid


async def _judge_faithfulness(
    question: str,
    answer: str,
    evidence: list[dict],
) -> tuple[bool | None, str]:
    if not answer or not evidence:
        return None, "No answer or evidence to judge."

    llm_evidence = minimize_evidence_for_llm(evidence, question)
    evidence_payload = [
        {
            "evidence_id": e.get("evidence_id"),
            "source_id": e.get("source_id"),
            "chunk": e.get("chunk"),
        }
        for e in llm_evidence
    ]

    system_msg = (
        "You are a compliance evaluator. Determine if the answer is fully supported by the evidence. "
        "If any claim is not supported, mark is_faithful=false. "
        "Return JSON only."
    )
    user_payload = {
        "question": question,
        "answer": answer,
        "evidence": evidence_payload,
    }

    text_config: ResponseTextConfigParam = {"format": FAITHFULNESS_FORMAT, "verbosity": "low"}

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

    is_faithful = payload.get("is_faithful")
    rationale = payload.get("rationale")
    if not isinstance(is_faithful, bool):
        is_faithful = None
    if not isinstance(rationale, str):
        rationale = ""

    return is_faithful, rationale


def _heuristic_faithfulness(citations: list[int], evidence_count: int) -> bool | None:
    if not citations:
        return None
    return all(1 <= int(c) <= evidence_count for c in citations)


async def run_faithfulness(payload: RagEvalFaithfulnessRequest) -> RagEvalFaithfulnessResponse:
    async with T4DbSession() as session:
        logger.info("===faith:db_session_open")
        run = RAGEvalRunDB(
            embedding_version=f"{EMBED_MODEL}/384",
            model_version="rag-eval-faithfulness",
            description=payload.description,
        )
        session.add(run)
        await session.flush()
        logger.info("===faith:run_created run_id=%s", str(run.id)[:5])

        stmt = select(RAGEvalDatasetDB).where(RAGEvalDatasetDB.is_active.is_(True))
        if payload.category and payload.category.lower() != "rag":
            stmt = stmt.where(RAGEvalDatasetDB.category == payload.category)
        if payload.limit:
            stmt = stmt.limit(payload.limit)

        dataset_rows = (await session.execute(stmt)).scalars().all()
        logger.info("===faith:dataset_loaded count=%s", len(dataset_rows))
        if not dataset_rows:
            raise HTTPException(status_code=404, detail="No active dataset rows found.")

        results: list[RAGEvalResultDB] = []
        rows: list[RagEvalFaithfulnessRow] = []
        current_ten_id = None
        faith_values: list[float | None] = []

        for idx, row in enumerate(dataset_rows, start=1):
            logger.info("===faith:row_start dataset_id=%s", str(row.id)[:5])
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
                logger.info("===faith:tenant_switch ten_id=%s", str(ten_id)[:5])

            zme = ZMeDataClass(ztid=ten_id, zbid=biz_id, zuid=user_id, zdb=session)

            rag_payload = RagQueryRequest(query=row.question, top_k=payload.top_k)
            logger.info("===faith:embedding_start")
            rag_response = await rag_answer_rerank(rag_payload, zme)
            evidence = (rag_response or {}).get("evidence") or []
            retrieved_ids = [str(e.get("source_id")) for e in evidence if e.get("source_id")]
            answer_text = (rag_response or {}).get("answer") or ""
            citations = (rag_response or {}).get("citations") or []

            if payload.judge:
                is_faithful, judge_note = await _judge_faithfulness(
                    row.question,
                    answer_text,
                    evidence,
                )
                judge_mode = "llm"
            else:
                is_faithful = _heuristic_faithfulness(citations, len(evidence))
                judge_note = "heuristic" if is_faithful is not None else "no_citations"
                judge_mode = "heuristic"

            results.append(
                RAGEvalResultDB(
                    dataset_id=row.id,
                    run_id=run.id,
                    retrieved_source_ids=retrieved_ids,
                    answer=answer_text,
                    recall_at_k=None,
                    precision_at_k=None,
                    is_correct=None,
                    is_faithful=is_faithful,
                    eval_notes=json.dumps(
                        {
                            "metric": "faithfulness",
                            "top_k": payload.top_k,
                            "judge": judge_mode,
                            "judge_note": judge_note,
                        },
                        ensure_ascii=False,
                    ),
                )
            )

            row_out = RagEvalFaithfulnessRow(
                run_id=str(run.id),
                dataset_id=str(row.id),
                question=row.question,
                answer=answer_text,
                retrieved_source_ids=retrieved_ids,
                citations=[int(c) for c in citations],
                is_faithful=is_faithful,
                top_k=payload.top_k,
                judge=judge_mode,
            )
            if payload.include_rows:
                rows.append(row_out)

            faith_values.append(
                1.0 if is_faithful is True else (0.0 if is_faithful is False else None)
            )
            logger.info(
                "===faith:row_done idx=%s dataset_id=%s",
                idx,
                str(row.id),
            )

        if results:
            logger.info("===faith:db_add_results count=%s", len(results))
            session.add_all(results)
        logger.info("===faith:db_commit start")
        await session.commit()
        logger.info(
            "===faith:committed run_id=%s results=%s",
            str(run.id),
            len(results),
        )

        avg_faith = ru.avg(faith_values)
        total = len(rows) if payload.include_rows else len(results)

        response = RagEvalFaithfulnessResponse(
            run_id=str(run.id),
            description=payload.description,
            top_k=payload.top_k,
            total=total,
            avg_faithfulness=avg_faith,
            rows=rows if payload.include_rows else None,
        )
        logger.info(
            "===faith:done run_id=%s total=%s avg_faith=%s",
            str(run.id),
            total,
            f"{avg_faith:.4f}" if avg_faith is not None else "None",
        )
        logger.info("===faith:db_session_close")
        return response
