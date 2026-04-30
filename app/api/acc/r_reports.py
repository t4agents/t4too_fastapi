from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import UserContext, get_current_user, get_db
from app.services.accounting import balance_sheet, export_tax_package_zip, income_statement, ledger_rows, trial_balance

router = APIRouter(tags=["reports"])


@router.get("/ledger/general")
def get_general_ledger(
    account_id: UUID | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
) -> dict:
    rows = []
    running = {}
    for entry_date, acct_id, code, name, acct_type, line_type, amount in ledger_rows(
        db, user.owner_id, from_date=from_date, to_date=to_date, account_id=account_id
    ):
        current = running.get(acct_id, 0)
        delta = float(amount) if line_type == "debit" else -float(amount)
        current += delta
        running[acct_id] = current
        rows.append(
            {
                "entry_date": entry_date,
                "account_id": acct_id,
                "code": code,
                "name": name,
                "account_type": acct_type,
                "line_type": line_type,
                "amount": amount,
                "running_balance": current,
            }
        )
    return {"rows": rows}


@router.get("/reports/trial-balance")
def get_trial_balance(
    period_yyyymm: int | None = Query(default=None),
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
) -> dict:
    from_date = to_date = None
    if period_yyyymm:
        year = period_yyyymm // 100
        month = period_yyyymm % 100
        from_date = date(year, month, 1)
        to_date = date(year, month, 28)
        while True:
            try:
                to_date = to_date.replace(day=to_date.day + 1)
            except ValueError:
                break
    return {"rows": trial_balance(db, user.owner_id, from_date=from_date, to_date=to_date)}


@router.get("/reports/balance-sheet")
def get_balance_sheet(
    as_of: date,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
) -> dict:
    return balance_sheet(db, user.owner_id, as_of)


@router.get("/reports/income-statement")
def get_income_statement(
    from_date: date,
    to_date: date,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
) -> dict:
    return income_statement(db, user.owner_id, from_date, to_date)


@router.get("/reports/export-tax-package")
def get_export_tax_package(
    period_yyyymm: int,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
) -> StreamingResponse:
    data = export_tax_package_zip(db, user.owner_id, period_yyyymm)
    return StreamingResponse(
        iter([data]),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=tax_package_{period_yyyymm}.zip"},
    )

