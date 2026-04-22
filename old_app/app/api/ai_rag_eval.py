from fastapi import APIRouter

from app.rag.eva.answer_relevance import run_answer_relevance
from app.rag.eva.answer_similarity import run_answer_similarity
from app.rag.eva.faithfulness import run_faithfulness
from app.rag.eva.precision_at_k import run_precision_at_k
from app.rag.eva.recall_at_k import run_recall_at_k
from app.schemas.sch_ai_rag_eval import RagEvalRequest, RagEvalResponse
from app.schemas.sch_ai_rag_answer_similarity import (
    RagEvalAnswerSimilarityRequest,
    RagEvalAnswerSimilarityResponse,
)
from app.schemas.sch_ai_rag_answer_relevance import (
    RagEvalAnswerRelevanceRequest,
    RagEvalAnswerRelevanceResponse,
)
from app.schemas.sch_ai_rag_overall import RagEvalOverallRequest, RagEvalOverallResponse
from app.schemas.sch_ai_rag_run_rfr import RagEvalRunRFRRequest, RagEvalRunRFRResponse
from app.schemas.sch_ai_rag_faithfulness import (
    RagEvalFaithfulnessRequest,
    RagEvalFaithfulnessResponse,
)
from app.schemas.sch_ai_rag_precision import RagEvalPrecisionRequest, RagEvalPrecisionResponse
from app.schemas.sch_ai_rag_recall import RagEvalRecallRequest, RagEvalRecallResponse
from app.service.ser_ai_rag_eval import run_rag_eval


ragEvalRou = APIRouter()


@ragEvalRou.post("/run", response_model=RagEvalResponse)
async def run_rag_eval_endpoint(payload: RagEvalRequest):
    return await run_rag_eval(payload)


@ragEvalRou.post("/run-judge", response_model=RagEvalResponse)
async def run_rag_eval_judge_endpoint(payload: RagEvalRequest):
    judge_payload = payload.model_copy(update={"judge": True})
    return await run_rag_eval(judge_payload)


@ragEvalRou.post("/run-heuristic", response_model=RagEvalResponse)
async def run_rag_eval_heuristic_endpoint(payload: RagEvalRequest):
    heuristic_payload = payload.model_copy(update={"judge": False})
    return await run_rag_eval(heuristic_payload)


@ragEvalRou.post("/run-summary", response_model=RagEvalResponse)
async def run_rag_eval_summary_endpoint(payload: RagEvalRequest):
    summary_payload = payload.model_copy(
        update={"include_rows": False, "include_failures": False}
    )
    return await run_rag_eval(summary_payload)


@ragEvalRou.post("/recall_at_k", response_model=RagEvalRecallResponse)
async def run_rag_eval_recall_at_k_endpoint(payload: RagEvalRecallRequest):
    return await run_recall_at_k(payload)


@ragEvalRou.post("/precision_at_k", response_model=RagEvalPrecisionResponse)
async def run_rag_eval_precision_at_k_endpoint(payload: RagEvalPrecisionRequest):
    return await run_precision_at_k(payload)


@ragEvalRou.post("/faithfulness", response_model=RagEvalFaithfulnessResponse)
async def run_rag_eval_faithfulness_endpoint(payload: RagEvalFaithfulnessRequest):
    return await run_faithfulness(payload)


@ragEvalRou.post("/answer_similarity", response_model=RagEvalAnswerSimilarityResponse)
async def run_rag_eval_answer_similarity_endpoint(
    payload: RagEvalAnswerSimilarityRequest,
):
    return await run_answer_similarity(payload)


@ragEvalRou.post("/answer_relevance", response_model=RagEvalAnswerRelevanceResponse)
async def run_rag_eval_answer_relevance_endpoint(
    payload: RagEvalAnswerRelevanceRequest,
):
    return await run_answer_relevance(payload)


@ragEvalRou.post("/run_recall_faithfulness_relevance", response_model=RagEvalRunRFRResponse)
async def run_rag_eval_recall_faithfulness_relevance_endpoint(
    payload: RagEvalRunRFRRequest,
):
    recall_payload = RagEvalRecallRequest(
        top_k=payload.top_k,
        limit=payload.limit,
        category=payload.category,
        description=f"{payload.description} (recall@k)",
        include_rows=payload.include_rows,
    )
    faith_payload = RagEvalFaithfulnessRequest(
        top_k=payload.top_k,
        limit=payload.limit,
        category=payload.category,
        description=f"{payload.description} (faithfulness)",
        judge=payload.judge,
        include_rows=payload.include_rows,
    )
    relevance_payload = RagEvalAnswerRelevanceRequest(
        top_k=payload.top_k,
        limit=payload.limit,
        category=payload.category,
        description=f"{payload.description} (relevance)",
        include_rows=payload.include_rows,
    )

    recall = await run_recall_at_k(recall_payload)
    faithfulness = await run_faithfulness(faith_payload)
    relevance = await run_answer_relevance(relevance_payload)

    return RagEvalRunRFRResponse(
        recall=recall,
        faithfulness=faithfulness,
        relevance=relevance,
    )


@ragEvalRou.post("/run_overall_score", response_model=RagEvalOverallResponse)
async def run_rag_eval_overall_score_endpoint(
    payload: RagEvalOverallRequest,
):
    recall_payload = RagEvalRecallRequest(
        top_k=payload.top_k,
        limit=payload.limit,
        category=payload.category,
        description=f"{payload.description} (recall@k)",
        include_rows=False,
    )
    faith_payload = RagEvalFaithfulnessRequest(
        top_k=payload.top_k,
        limit=payload.limit,
        category=payload.category,
        description=f"{payload.description} (faithfulness)",
        judge=payload.judge,
        include_rows=False,
    )
    relevance_payload = RagEvalAnswerRelevanceRequest(
        top_k=payload.top_k,
        limit=payload.limit,
        category=payload.category,
        description=f"{payload.description} (relevance)",
        include_rows=False,
    )

    recall = await run_recall_at_k(recall_payload)
    faithfulness = await run_faithfulness(faith_payload)
    relevance = await run_answer_relevance(relevance_payload)

    recall_avg = recall.avg_recall_at_k
    faith_avg = faithfulness.avg_faithfulness
    relevance_avg = relevance.avg_answer_relevance

    weights = {
        "recall": payload.recall_weight,
        "faithfulness": payload.faithfulness_weight,
        "relevance": payload.relevance_weight,
    }

    weighted_sum = 0.0
    weight_total = 0.0
    for name, value, weight in [
        ("recall", recall_avg, payload.recall_weight),
        ("faithfulness", faith_avg, payload.faithfulness_weight),
        ("relevance", relevance_avg, payload.relevance_weight),
    ]:
        if value is None or weight <= 0:
            continue
        weighted_sum += value * weight
        weight_total += weight

    overall_score = None if weight_total == 0 else weighted_sum / weight_total

    return RagEvalOverallResponse(
        overall_score=overall_score,
        recall_avg=recall_avg,
        faithfulness_avg=faith_avg,
        relevance_avg=relevance_avg,
        weights=weights,
        run_ids={
            "recall": recall.run_id,
            "faithfulness": faithfulness.run_id,
            "relevance": relevance.run_id,
        },
    )
