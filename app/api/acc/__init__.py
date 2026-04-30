from fastapi import APIRouter

from app.api import r_accounts, r_coa, r_health, r_je_drafts, r_journal_entries, r_periods, r_reports, r_transactions

api_router = APIRouter()
api_router.include_router(r_health.router)
api_router.include_router(r_coa.router)
api_router.include_router(r_accounts.router)
api_router.include_router(r_transactions.router)
api_router.include_router(r_je_drafts.router)
api_router.include_router(r_journal_entries.router)
api_router.include_router(r_reports.router)
api_router.include_router(r_periods.router)
