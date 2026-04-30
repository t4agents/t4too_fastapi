from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@router.get("/ai/principles")
def ai_principles() -> dict[str, list[str]]:
    return {
        "principles": [
            "AI-first: workflows begin with AI proposals.",
            "AI-internal: reasoning and confidence are stored with each draft.",
            "AI-inherited: each action keeps a chain from source transaction to posted ledger.",
            "Human approval is mandatory before posting.",
        ]
    }

