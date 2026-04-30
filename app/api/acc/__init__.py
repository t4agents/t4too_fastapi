from fastapi import APIRouter

from . import r_accounts, r_coa, r_health, r_je_drafts, r_journal_entries, r_periods, r_reports, r_transactions

rouAcc = APIRouter()
rouAcc.include_router(r_health.router)
rouAcc.include_router(r_coa.router)
rouAcc.include_router(r_accounts.router)
rouAcc.include_router(r_transactions.router)
rouAcc.include_router(r_je_drafts.router)
rouAcc.include_router(r_journal_entries.router)
rouAcc.include_router(r_reports.router)
rouAcc.include_router(r_periods.router)
