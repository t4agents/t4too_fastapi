from __future__ import annotations

import json

from fastapi import HTTPException
from openai import AsyncOpenAI
from openai.types.responses.response_format_text_json_schema_config_param import (
    ResponseFormatTextJSONSchemaConfigParam,
)
from openai.types.responses.response_text_config_param import ResponseTextConfigParam
from sqlalchemy import select

from app.config import get_settings_singleton
from app.db.models.ai.ai_gold_dataset import RAGEvalDatasetDB, RAGEvalResultDB, RAGEvalRunDB
from app.llm.conn.openai_embedder import EMBED_MODEL
from app.schemas.sch_ai_rag_basic import QueryReq
from app.schemas.sch_ai_rag_answer_relevance import (
    RagEvalAnswerRelevanceRequest,
    RagEvalAnswerRelevanceResponse,
    RagEvalAnswerRelevanceRow,
)

# from app.service.ser_ai_embedding import rag_answer_rerank

settings = get_settings_singleton()
oai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
JUDGE_MODEL = "gpt-5-mini"

RELEVANCE_FORMAT: ResponseFormatTextJSONSchemaConfigParam = {
    "type": "json_schema",
    "name": "answer_relevance_judgement",
    "description": "Judge if answer is relevant to question and expected answer.",
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


def _avg(values: list[float | None]) -> float | None:
    nums = [v for v in values if isinstance(v, (int, float))]
    if not nums:
        return None
    return sum(nums) / len(nums)


async def _judge_relevance(question: str, answer: str, expected: str) -> tuple[bool | None, str]:
    if not answer or not expected or not question:
        return None, "missing_question_answer_or_expected"
    text_config: ResponseTextConfigParam = {"format": RELEVANCE_FORMAT, "verbosity": "low"}
    response = await oai_client.responses.create(
        model=JUDGE_MODEL,
        input=[
            {"role": "system", "content": "Judge whether answer is relevant to question and expected answer."},
            {"role": "user", "content": json.dumps({"question": question, "expected_answer": expected, "answer": answer})},
        ],
        text=text_config,
        reasoning={"summary": "auto"},
    )
    try:
        payload = json.loads(response.output_text or "")
    except json.JSONDecodeError:
        return None, "Judge output not valid JSON."
    is_relevant = payload.get("is_relevant")
    rationale = payload.get("rationale")
    return (is_relevant if isinstance(is_relevant, bool) else None), (rationale if isinstance(rationale, str) else "")


async def run_answer_relevance(payload: RagEvalAnswerRelevanceRequest, zjwt: JWType) -> RagEvalAnswerRelevanceResponse:
    run = RAGEvalRunDB(
        embedding_version=f"{EMBED_MODEL}/384",
        model_version="rag-eval-answer-relevance",
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
    rows: list[RagEvalAnswerRelevanceRow] = []
    relevance_values: list[float | None] = []

    for row in dataset_rows:
        rag_payload = QueryReq(query=row.question, top_k=payload.top_k)
        rag_response = await rag_answer_rerank(rag_payload, ctx)
        answer_text = (rag_response or {}).get("answer") or ""
        is_relevant, relevance_note = await _judge_relevance(row.question, answer_text, row.expected_answer or "")

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
                    {"metric": "answer_relevance", "top_k": payload.top_k, "relevance_note": relevance_note, "judge": "llm"},
                    ensure_ascii=False,
                ),
            )
        )
        if payload.include_rows:
            rows.append(
                RagEvalAnswerRelevanceRow(
                    run_id=str(run.id),
                    dataset_id=str(row.id),
                    question=row.question,
                    expected_answer=row.expected_answer or "",
                    answer=answer_text,
                    is_relevant=is_relevant,
                    relevance_note=relevance_note,
                    top_k=payload.top_k,
                )
            )
        relevance_values.append(1.0 if is_relevant is True else (0.0 if is_relevant is False else None))

    if results:
        add_all(results)
    await flush()

    total = len(rows) if payload.include_rows else len(results)
    return RagEvalAnswerRelevanceResponse(
        run_id=str(run.id),
        description=payload.description,
        top_k=payload.top_k,
        total=total,
        avg_answer_relevance=_avg(relevance_values),
        rows=rows if payload.include_rows else None,
    )
