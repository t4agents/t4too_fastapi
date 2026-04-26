from __future__ import annotations

from openai import AsyncOpenAI

from app.config import get_settings_singleton

settings = get_settings_singleton()
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

EMBED_MODEL = "text-embedding-3-small"
EMBED_MODEL_LG = "text-embedding-3-large"


async def embed_fn(text: str) -> list[float]:
    response = await client.embeddings.create(
        model=EMBED_MODEL,
        input=text,
        dimensions=384,
    )
    return response.data[0].embedding



async def embed_fn_lg(text: str) -> list[float]:
    response = await client.embeddings.create(
        model=EMBED_MODEL_LG,
        input=text,
        dimensions=1024,
    )
    return response.data[0].embedding
