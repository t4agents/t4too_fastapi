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
from app.schemas.sch_ai_embedding import RagQueryRequest
from app.schemas.sch_ai_rag_faithfulness import (
    RagEvalFaithfulnessRequest,
    RagEvalFaithfulnessResponse,
    RagEvalFaithfulnessRow,
)
from app.service.ser_ai_context import AIContext
from app.service.ser_ai_embedding import minimize_evidence_for_llm, rag_answer_rerank

settings = get_settings_singleton()
oai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
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


def _avg(values: list[float | None]) -> float | None:
    nums = [v for v in values if isinstance(v, (int, float))]
    if not nums:
        return None
    return sum(nums) / len(nums)


async def _judge_faithfulness(question: str, answer: str, evidence: list[dict]) -> tuple[bool | None, str]:
    if not answer or not evidence:
        return None, "No answer or evidence to judge."
    llm_evidence = minimize_evidence_for_llm(evidence, question)
    text_config: ResponseTextConfigParam = {"format": FAITHFULNESS_FORMAT, "verbosity": "low"}
    response = await oai_client.responses.create(
        model=JUDGE_MODEL,
        input=[
            {"role": "system", "content": "Judge if answer is fully supported by evidence. Return JSON only."},
            {"role": "user", "content": json.dumps({"question": question, "answer": answer, "evidence": llm_evidence})},
        ],
        text=text_config,
        reasoning={"summary": "auto"},
    )
    try:
        payload = json.loads(response.output_text or "")
    except json.JSONDecodeError:
        return None, "Judge output not valid JSON."
    is_faithful = payload.get("is_faithful")
    rationale = payload.get("rationale")
    return (is_faithful if isinstance(is_faithful, bool) else None), (rationale if isinstance(rationale, str) else "")


def _heuristic_faithfulness(citations: list[int], evidence_count: int) -> bool | None:
    if not citations:
        return None
    return all(1 <= int(c) <= evidence_count for c in citations)


async def run_faithfulness(payload: RagEvalFaithfulnessRequest, ctx: AIContext) -> RagEvalFaithfulnessResponse:
    run = RAGEvalRunDB(
        embedding_version=f"{EMBED_MODEL}/384",
        model_version="rag-eval-faithfulness",
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
    rows: list[RagEvalFaithfulnessRow] = []
    faith_values: list[float | None] = []

    for row in dataset_rows:
        rag_payload = RagQueryRequest(query=row.question, top_k=payload.top_k)
        rag_response = await rag_answer_rerank(rag_payload, ctx)
        evidence = (rag_response or {}).get("evidence") or []
        retrieved_ids = [str(e.get("source_id")) for e in evidence if e.get("source_id")]
        answer_text = (rag_response or {}).get("answer") or ""
        citations = (rag_response or {}).get("citations") or []

        if payload.judge:
            is_faithful, judge_note = await _judge_faithfulness(row.question, answer_text, evidence)
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
                    {"metric": "faithfulness", "top_k": payload.top_k, "judge": judge_mode, "judge_note": judge_note},
                    ensure_ascii=False,
                ),
            )
        )
        if payload.include_rows:
            rows.append(
                RagEvalFaithfulnessRow(
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
            )
        faith_values.append(1.0 if is_faithful is True else (0.0 if is_faithful is False else None))

    if results:
        ctx.db.add_all(results)
    await ctx.db.flush()

    total = len(rows) if payload.include_rows else len(results)
    return RagEvalFaithfulnessResponse(
        run_id=str(run.id),
        description=payload.description,
        top_k=payload.top_k,
        total=total,
        avg_faithfulness=_avg(faith_values),
        rows=rows if payload.include_rows else None,
    )
