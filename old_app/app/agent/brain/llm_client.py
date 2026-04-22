from openai import AsyncOpenAI

from app.config import get_settings_singleton

settings = get_settings_singleton()
oai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


def extract_reasoning_summaries(response) -> list[str]:
    summaries: list[str] = []
    for item in getattr(response, "output", []) or []:
        if getattr(item, "type", None) != "reasoning":
            continue
        for s in getattr(item, "summary", []) or []:
            if getattr(s, "type", None) == "summary_text":
                summaries.append(s.text)
    return summaries
