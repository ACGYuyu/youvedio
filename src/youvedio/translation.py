"""DeepSeek / OpenAI-compatible translation service."""

from __future__ import annotations

from youvedio.config import settings


def translate_query(text: str) -> dict[str, str]:
    """Translate a query into zh/en/ja using DeepSeek."""
    if not settings.deepseek_api_key:
        return {"zh": text, "en": text, "ja": text}
    # TODO: implement actual translation call
    return {"zh": text, "en": text, "ja": text}
