"""DeepSeek / OpenAI-compatible multi-language translation service."""

from __future__ import annotations

import logging

import httpx

from youvedio.config import settings

logger = logging.getLogger(__name__)

TRANSLATION_PROMPT = (
    "You are a translation assistant for a torrent search engine. "
    "Given a search query, translate it into Chinese, English, and Japanese. "
    "Return ONLY a JSON object with keys 'zh', 'en', 'ja'. "
    "If the query is already in a language, keep it as-is in that field. "
    "Do not add explanations or markdown."
)


def translate_query(text: str) -> dict[str, str]:
    """Translate query into zh/en/ja using DeepSeek (OpenAI-compatible).

    Returns a dict with keys 'zh', 'en', 'ja'. Falls back to original
    text for all languages if API is unavailable.
    """
    if not text.strip():
        return {"zh": text, "en": text, "ja": text}

    if not settings.deepseek_api_key:
        logger.info("No DeepSeek API key configured — skipping translation")
        return _guess_languages(text)

    try:
        result = _call_api(text)
        if result and all(k in result for k in ("zh", "en", "ja")):
            return result
    except Exception as e:
        logger.warning("Translation API call failed: %s", e)

    return _guess_languages(text)


def _call_api(text: str) -> dict[str, str] | None:
    """Call DeepSeek API (OpenAI-compatible endpoint)."""
    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.deepseek_model,
        "messages": [
            {"role": "system", "content": TRANSLATION_PROMPT},
            {"role": "user", "content": text},
        ],
        "temperature": 0.1,
        "max_tokens": 256,
    }

    with httpx.Client(timeout=15.0) as client:
        resp = client.post(
            f"{settings.deepseek_base_url.rstrip('/')}/chat/completions",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        body = resp.json()
        content = body["choices"][0]["message"]["content"]

    import json as json_mod

    # Try direct JSON parse first
    try:
        return json_mod.loads(content)
    except json_mod.JSONDecodeError:
        pass

    # Fallback: extract JSON block from markdown
    import re

    m = re.search(r"\{[^}]+\}", content, re.DOTALL)
    if m:
        try:
            return json_mod.loads(m.group(0))
        except json_mod.JSONDecodeError:
            pass

    return None


def _guess_languages(text: str) -> dict[str, str]:
    """Fallback: use original text for all languages."""
    return {"zh": text, "en": text, "ja": text}
