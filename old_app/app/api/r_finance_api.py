# app/services/dividend_service.py
import secrets, os
from decimal import Decimal

from fastapi import APIRouter, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.db.db_sync import get_db_sync_contextmanager
from app.providers.finnhub_client import FinnhubClient
from app.db.repo.repo_div_inject import DividendRepo

#--------------------------------- secure
security = HTTPBasic()
def require_password(credentials: HTTPBasicCredentials = Depends(security),):
    correct_pass = secrets.compare_digest(credentials.password,os.environ["ADMIN_PASSWORD"],)
    if not correct_pass:return
AdminDeps = Depends(require_password)
#--------------------------------- secure

finApiRou = APIRouter()


@finApiRou.get("/finnhub", dependencies=[AdminDeps])
def finnhub_api(symbol: str) -> dict:
    client = FinnhubClient()
    data = client.get_quote_and_profile(symbol)
    return data

