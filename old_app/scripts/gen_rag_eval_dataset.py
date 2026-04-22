import argparse
import asyncio
import json
import os
import sys
from datetime import date
from decimal import Decimal
from typing import Iterable

from sqlalchemy import select, text

# Ensure repo root is on sys.path when running as a script
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


from app.db.db_async import T4DbSession
from app.db.models.ai_embedding import Embedding384
from app.db.models.ai_gold_dataset import RAGEvalDatasetDB
from app.db.models.m_payroll_history import PayrollHistory


def _fmt(value) -> str:
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _build_expected(row: PayrollHistory) -> str:
    parts = [
        f"full_name={_fmt(row.full_name)}",
        f"employment_type={_fmt(row.employment_type)}",
        f"period_key={_fmt(row.period_key)}",
        f"pay_date={_fmt(row.pay_date)}",
        f"gross={_fmt(row.gross)}",
        f"net={_fmt(row.net)}",
        f"deductions={_fmt(row.total_deduction)}",
        f"regular_hours={_fmt(row.regular_hours)}",
        f"overtime_hours={_fmt(row.overtime_hours)}",
        f"cpp={_fmt(row.cpp)}",
        f"ei={_fmt(row.ei)}",
        f"tax={_fmt(row.tax)}",
        f"status={_fmt(row.status)}",
        f"excluded={_fmt(row.excluded)}",
    ]
    return " | ".join(parts)


QUESTION_TEMPLATES: list[str] = [
    "Summarize the payroll record for {full_name} for period {period_key}.",
    "Provide the pay details for {full_name} in period {period_key} in plain language.",
    "Describe the earnings and deductions for {full_name} in period {period_key}.",
    "Explain the hours and pay breakdown for {full_name} for period {period_key}.",
    "State the payroll details for {full_name} for period {period_key} and pay date {pay_date}.",
]


def _build_question(row: PayrollHistory, idx: int) -> str:
    template = QUESTION_TEMPLATES[idx % len(QUESTION_TEMPLATES)]
    return template.format(
        full_name=row.full_name or "the employee",
        period_key=row.period_key,
        pay_date=_fmt(row.pay_date),
    )


def _sql_literal(text: str) -> str:
    return "'" + text.replace("'", "''") + "'"


def _emit_sql(rows: Iterable[RAGEvalDatasetDB]) -> str:
    values = []
    for row in rows:
        values.append(
            "("
            + ",".join(
                [
                    _sql_literal(str(row.id)),
                    _sql_literal(row.question),
                    _sql_literal(row.expected_answer),
                    _sql_literal(json.dumps(row.relevant_source_ids)),
                    _sql_literal(row.category or ""),
                    "NULL" if row.difficulty is None else str(row.difficulty),
                    "true" if row.is_active else "false",
                ]
            )
            + ")"
        )
    return (
        "INSERT INTO rag_eval_dataset "
        "(id, question, expected_answer, relevant_source_ids, category, difficulty, is_active)\n"
        "VALUES\n"
        + ",\n".join(values)
        + ";\n"
    )


async def _load_rows(limit: int) -> list[tuple[PayrollHistory, Embedding384]]:
    async with T4DbSession() as session:
        stmt = (
            select(PayrollHistory, Embedding384)
            .join(Embedding384, Embedding384.source_id == PayrollHistory.id)
            .order_by(PayrollHistory.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.all())


async def main() -> None:
    parser = argparse.ArgumentParser(description="Generate RAG eval dataset rows.")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--out", type=str, default="")
    parser.add_argument("--insert", action="store_true")
    args = parser.parse_args()

    rows = await _load_rows(args.limit)
    if not rows:
        raise SystemExit("No payroll_history rows with embeddings found.")

    dataset_rows: list[RAGEvalDatasetDB] = []
    for idx, (history, _) in enumerate(rows):
        dataset_rows.append(
            RAGEvalDatasetDB(
                question=_build_question(history, idx),
                expected_answer=_build_expected(history),
                relevant_source_ids=[str(history.id)],
                category="rag",
                difficulty=2 if idx % 3 else 3,
                is_active=True,
            )
        )

    sql_text = _emit_sql(dataset_rows)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(sql_text)

    if args.insert:
        async with T4DbSession() as session:
            session.add_all(dataset_rows)
            await session.commit()

    print(sql_text)


if __name__ == "__main__":
    asyncio.run(main())
