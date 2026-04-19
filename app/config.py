# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class _Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env",env_file_encoding="utf-8",extra="ignore",)

    TOO_SB_DB: str = "postgresql+asyncpg://username:pwd@local/icedb"
    JWKS_URL: str = "https://pjenyfvefvgbldgdegxs.supabase.co/auth/v1/.well-known/jwks.json"
    JWKS_ISS: str = "https://pjenyfvefvgbldgdegxs.supabase.co/auth/v1"
    JWKS_AUD: str = "authenticated"
    JWKS_ALG: list[str] = ["ES256", "RS256"]
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    # T4_ADMIN: str = "postgresql+asyncpg://username:pwd@local/icedb"
    # OPENAI_API_KEY: str =""
    # COHERE_API_KEY: str = ""
    # MODEL_PRICING_JSON: str = "{\"gpt-5-mini\": {\"input\": 0.15, \"output\": 0.60}}"
    # GUARDRAIL_ENABLE_LLM_JUDGE: bool = True
    # PII_MINIMIZE_RAG_EVIDENCE: bool = True

    # ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # STRIPE_SECRET_KEY: str = ""
    # STRIPE_WEBHOOK_SECRET: str = ""
    # STRIPE_SUCCESS_URL: str = "https://t4agents.com/billing/success"
    # STRIPE_CANCEL_URL: str = "https://t4agents.com/billing/cancel"
    # STRIPE_PORTAL_RETURN_URL: str = "https://t4agents.com/billing"

    # STRIPE_PRICE_BASIC_MONTH: str= "price_1TBOWrRwLzeE6kyCNFmHZzTp"
    # STRIPE_PRICE_BASIC_YEAR: str = "price_1TBOWrRwLzeE6kyCprGxdvWK"
    # STRIPE_PRICE_PRO_MONTH: str = "price_1TBOaiRwLzeE6kyCV57uGsvn"
    # STRIPE_PRICE_PRO_YEAR: str = "price_1TBOaiRwLzeE6kyCgHUak49W"
    # STRIPE_PRICE_ENTERPRISE_MONTH: str = "price_1TBOb9RwLzeE6kyCcAgDncr1"
    # STRIPE_PRICE_ENTERPRISE_YEAR: str = "price_1TBObXRwLzeE6kyCSWexfBjm"
    
@lru_cache()
def get_settings_singleton()-> _Settings:
    return _Settings()
