import argparse
import asyncio
import csv
import json
import os
import sys

# Ensure repo root is on sys.path when running as a script
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from app.schemas.sch_ai_rag_eval import RagEvalRequest
from app.service.ser_ai_rag_eval import run_rag_eval


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run RAG eval and store results.")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--category", type=str, default="rag")
    parser.add_argument("--description", type=str, default="RAG eval run")
    parser.add_argument("--judge", action="store_true")
    parser.add_argument("--no-evidence", action="store_true")
    parser.add_argument("--evidence-max-chars", type=int, default=500)
    parser.add_argument("--no-relevancy", action="store_true")
    parser.add_argument("--csv", type=str, default="")
    parser.add_argument("--csv-failures", type=str, default="")
    parser.add_argument("--json-out", type=str, default="")
    args = parser.parse_args()

    result = await run_rag_eval(
        RagEvalRequest(
            top_k=args.top_k,
            limit=args.limit,
            category=args.category,
            description=args.description,
            judge=args.judge,
            no_evidence=args.no_evidence,
            evidence_max_chars=args.evidence_max_chars,
            no_relevancy=args.no_relevancy,
            include_rows=True,
            include_failures=True,
        )
    )

    rows = result.rows or []
    failure_rows = result.failure_rows or []

    def _fmt_float(value: float | None) -> str:
        return "" if value is None else f"{value:.4f}"

    if args.csv:
        fieldnames = [
            "run_id",
            "dataset_id",
            "question",
            "expected_answer",
            "answer",
            "recall_at_k",
            "precision_at_k",
            "is_faithful",
            "answer_relevancy",
            "route",
            "model",
            "rerank_model",
            "top_k",
        ]
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(
                    {
                        "run_id": row.run_id,
                        "dataset_id": row.dataset_id,
                        "question": row.question,
                        "expected_answer": row.expected_answer,
                        "answer": row.answer,
                        "recall_at_k": _fmt_float(row.recall_at_k),
                        "precision_at_k": _fmt_float(row.precision_at_k),
                        "is_faithful": "" if row.is_faithful is None else str(row.is_faithful),
                        "answer_relevancy": _fmt_float(row.answer_relevancy),
                        "route": row.route or "",
                        "model": row.model or "",
                        "rerank_model": row.rerank_model or "",
                        "top_k": str(row.top_k),
                    }
                )
            summary_row = {
                "run_id": result.run_id,
                "dataset_id": "__SUMMARY__",
                "question": "__SUMMARY__",
                "expected_answer": "",
                "answer": "",
                "recall_at_k": _fmt_float(result.avg_recall_at_k),
                "precision_at_k": _fmt_float(result.avg_precision_at_k),
                "is_faithful": _fmt_float(result.avg_faithfulness),
                "answer_relevancy": _fmt_float(result.avg_answer_relevancy),
                "route": "",
                "model": "",
                "rerank_model": "",
                "top_k": str(args.top_k),
            }
            writer.writerow(summary_row)

    if args.csv_failures:
        fieldnames = [
            "run_id",
            "dataset_id",
            "question",
            "expected_answer",
            "answer",
            "recall_at_k",
            "precision_at_k",
            "is_faithful",
            "answer_relevancy",
            "route",
            "model",
            "rerank_model",
            "top_k",
        ]
        with open(args.csv_failures, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in failure_rows:
                writer.writerow(
                    {
                        "run_id": row.run_id,
                        "dataset_id": row.dataset_id,
                        "question": row.question,
                        "expected_answer": row.expected_answer,
                        "answer": row.answer,
                        "recall_at_k": _fmt_float(row.recall_at_k),
                        "precision_at_k": _fmt_float(row.precision_at_k),
                        "is_faithful": "" if row.is_faithful is None else str(row.is_faithful),
                        "answer_relevancy": _fmt_float(row.answer_relevancy),
                        "route": row.route or "",
                        "model": row.model or "",
                        "rerank_model": row.rerank_model or "",
                        "top_k": str(row.top_k),
                    }
                )

    if args.json_out:
        json_payload = {
            "run_id": result.run_id,
            "description": result.description,
            "top_k": result.top_k,
            "total": result.total,
            "failures": result.failures,
            "avg_recall_at_k": result.avg_recall_at_k,
            "avg_precision_at_k": result.avg_precision_at_k,
            "avg_faithfulness": result.avg_faithfulness,
            "avg_answer_relevancy": result.avg_answer_relevancy,
            "rows": [
                {
                    "dataset_id": row.dataset_id,
                    "question": row.question,
                    "recall_at_k": row.recall_at_k,
                    "precision_at_k": row.precision_at_k,
                    "is_faithful": row.is_faithful,
                    "answer_relevancy": row.answer_relevancy,
                    "route": row.route,
                }
                for row in rows
            ],
        }
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(json_payload, f, ensure_ascii=False, indent=2)

    print(f"Eval completed. run_id={result.run_id} rows={result.total}")


if __name__ == "__main__":
    asyncio.run(main())
