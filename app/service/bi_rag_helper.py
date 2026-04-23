from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from openai import AsyncOpenAI

from app.config import get_settings_singleton
from app.schemas.sch_ai import JWType

_settings = get_settings_singleton()
_client = AsyncOpenAI(api_key=_settings.OPENAI_API_KEY)
_EMBED_MODEL = "text-embedding-3-small"


def bi_extract_cli_id(zjwt: JWType) -> UUID:
    user_metadata = zjwt.get("user_metadata")
    if not isinstance(user_metadata, dict):
        raise HTTPException(status_code=400, detail="Missing user_metadata in JWT.")

    raw_cli_id = user_metadata.get("sbu_client_id")
    if raw_cli_id is None:
        raise HTTPException(status_code=400, detail="Missing sbu_client_id in JWT user_metadata.")

    try:
        return UUID(str(raw_cli_id))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid sbu_client_id UUID.") from exc


async def bi_embed_query_text(query: str) -> list[float]:
    response = await _client.embeddings.create(
        model=_EMBED_MODEL,
        input=query,
        dimensions=384,
    )
    embedding = response.data[0].embedding
    return [float(value) for value in embedding]


def bi_vector_literal(vector: list[float]) -> str:
    return "[" + ",".join(f"{value:.12g}" for value in vector) + "]"
