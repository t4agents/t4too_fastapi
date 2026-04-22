import json
import math
from datetime import date
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select, text

from app.agent.brain.llm_client import oai_client
from app.core.dependency_injection import ZMeDataClass
from app.db.db_async import T4DbSession
from app.db.models.ai_gold_dataset import RAGEvalDatasetDB, RAGEvalResultDB, RAGEvalRunDB
from app.db.models.m_payroll_history import PayrollHistory
from app.llm.conn.openai_embedder import EMBED_MODEL, embed_fn
from app.schemas.sch_ai_embedding import RagQueryRequest
from app.schemas.sch_ai_rag_eval import RagEvalRequest, RagEvalResponse, RagEvalRow
from app.service.ser_ai_embedding import rag_answer_rerank
from app.service.ser_ai_embedding import minimize_evidence_for_llm
from openai.types.responses.response_format_text_json_schema_config_param import (
    ResponseFormatTextJSONSchemaConfigParam,
)
from openai.types.responses.response_text_config_param import ResponseTextConfigParam


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


def _fmt(value) -> str:
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _intersection_count(a: list[str], b: list[str]) -> int:
    return len(set(a) & set(b))


def _truncate(text_value: str, max_chars: int) -> str:
    if not text_value:
        return ""
    if len(text_value) <= max_chars:
        return text_value
    return f"{text_value[:max_chars]}...(truncated {len(text_value) - max_chars} chars)"


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


def _avg(values: list[float | None]) -> float | None:
    nums = [v for v in values if isinstance(v, (int, float))]
    if not nums:
        return None
    return sum(nums) / len(nums)


def _is_failure(
    recall_at_k: float | None,
    precision_at_k: float | None,
    is_faithful: bool | None,
) -> bool:
    if recall_at_k is not None and recall_at_k < 1.0:
        return True
    if precision_at_k is not None and precision_at_k < 1.0:
        return True
    if is_faithful is False:
        return True
    return False


async def _get_context(session, source_id: str):
    result = await session.execute(
        select(PayrollHistory).where(PayrollHistory.id == source_id)
    )
    row = result.scalar_one_or_none()
    if not row:
        return None, None, None
    zuid = row.owner_id or row.created_by or row.employee_id
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


async def _answer_relevancy(answer: str, expected: str) -> tuple[float | None, str]:
    if not answer or not expected:
        return None, "missing_answer_or_expected"
    try:
        vec_answer = await embed_fn(answer)
        vec_expected = await embed_fn(expected)
        score = _cosine_similarity(vec_answer, vec_expected)
        return score, "ok" if score is not None else "invalid_vectors"
    except Exception as exc:
        return None, f"embed_error:{str(exc)}"


async def run_rag_eval(payload: RagEvalRequest) -> RagEvalResponse:
    async with T4DbSession() as session:
        run = RAGEvalRunDB(
            embedding_version=f"{EMBED_MODEL}/384",
            model_version="rag-eval",
            description=payload.description,
        )
        session.add(run)
        await session.flush()

        stmt = select(RAGEvalDatasetDB).where(RAGEvalDatasetDB.is_active.is_(True))
        if payload.category:
            stmt = stmt.where(RAGEvalDatasetDB.category == payload.category)
        if payload.limit:
            stmt = stmt.limit(payload.limit)

        dataset_rows = (await session.execute(stmt)).scalars().all()
        if not dataset_rows:
            raise HTTPException(status_code=404, detail="No active dataset rows found.")

        results: list[RAGEvalResultDB] = []
        rows: list[RagEvalRow] = []
        failure_rows: list[RagEvalRow] = []
        current_ten_id = None

        recall_values: list[float | None] = []
        precision_values: list[float | None] = []
        faith_values: list[float | None] = []
        relevancy_values: list[float | None] = []

        for row in dataset_rows:
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

            zme = ZMeDataClass(ztid=ten_id, zbid=biz_id, zuid=user_id, zdb=session)

            rag_payload = RagQueryRequest(query=row.question, top_k=payload.top_k)
            rag_response = await rag_answer_rerank(rag_payload, zme)
            evidence = (rag_response or {}).get("evidence") or []
            retrieved_ids = [str(e.get("source_id")) for e in evidence if e.get("source_id")]

            hit_count = _intersection_count(relevant_ids, retrieved_ids)
            recall_at_k = hit_count / max(len(set(relevant_ids)), 1)
            precision_at_k = hit_count / max(payload.top_k, 1)

            answer_text = (rag_response or {}).get("answer") or ""

            is_faithful = None
            judge_note = ""
            if payload.judge:
                is_faithful, judge_note = await _judge_faithfulness(row.question, answer_text, evidence)
            else:
                citations = (rag_response or {}).get("citations") or []
                if citations:
                    is_faithful = all(1 <= int(c) <= len(evidence) for c in citations)
                else:
                    is_faithful = None
                judge_note = "heuristic" if is_faithful is not None else "no_citations"

            answer_relevancy = None
            relevancy_note = "skipped"
            if not payload.no_relevancy:
                answer_relevancy, relevancy_note = await _answer_relevancy(
                    answer_text,
                    row.expected_answer or "",
                )

            evidence_snapshot = []
            if not payload.no_evidence:
                for e in evidence:
                    evidence_snapshot.append(
                        {
                            "evidence_id": e.get("evidence_id"),
                            "source_id": e.get("source_id"),
                            "score": e.get("score"),
                            "chunk": _truncate(str(e.get("chunk") or ""), payload.evidence_max_chars),
                        }
                    )

            eval_notes = {
                "route": (rag_response or {}).get("route", "rag"),
                "model": (rag_response or {}).get("model"),
                "rerank_model": (rag_response or {}).get("rerank_model"),
                "top_k": payload.top_k,
                "biz_id": _fmt(biz_id),
                "judge": "llm" if payload.judge else "heuristic",
                "judge_note": judge_note,
                "answer_relevancy": answer_relevancy,
                "relevancy_note": relevancy_note,
                "evidence": evidence_snapshot,
            }

            results.append(
                RAGEvalResultDB(
                    dataset_id=row.id,
                    run_id=run.id,
                    retrieved_source_ids=retrieved_ids,
                    answer=answer_text,
                    recall_at_k=recall_at_k,
                    precision_at_k=precision_at_k,
                    is_faithful=is_faithful,
                    eval_notes=json.dumps(eval_notes, ensure_ascii=False),
                )
            )

            row_out = RagEvalRow(
                run_id=str(run.id),
                dataset_id=str(row.id),
                question=row.question,
                expected_answer=row.expected_answer or "",
                answer=answer_text,
                recall_at_k=recall_at_k,
                precision_at_k=precision_at_k,
                is_faithful=is_faithful,
                answer_relevancy=answer_relevancy,
                route=(rag_response or {}).get("route", "rag"),
                model=(rag_response or {}).get("model"),
                rerank_model=(rag_response or {}).get("rerank_model"),
                top_k=payload.top_k,
            )
            if payload.include_rows:
                rows.append(row_out)
            if payload.include_failures and _is_failure(recall_at_k, precision_at_k, is_faithful):
                failure_rows.append(row_out)

            recall_values.append(recall_at_k)
            precision_values.append(precision_at_k)
            faith_values.append(1.0 if is_faithful is True else (0.0 if is_faithful is False else None))
            relevancy_values.append(answer_relevancy)

        if results:
            session.add_all(results)
        await session.commit()

        avg_recall = _avg(recall_values)
        avg_precision = _avg(precision_values)
        avg_faith = _avg(faith_values)
        avg_relevancy = _avg(relevancy_values)

        total = len(rows) if payload.include_rows else len(results)
        failures = len(failure_rows) if payload.include_failures else sum(
            1 for r in results if _is_failure(r.recall_at_k, r.precision_at_k, r.is_faithful)
        )

        return RagEvalResponse(
            run_id=str(run.id),
            description=payload.description,
            top_k=payload.top_k,
            total=total,
            failures=failures,
            avg_recall_at_k=avg_recall,
            avg_precision_at_k=avg_precision,
            avg_faithfulness=avg_faith,
            avg_answer_relevancy=avg_relevancy,
            rows=rows if payload.include_rows else None,
            failure_rows=failure_rows if payload.include_failures else None,
        )
