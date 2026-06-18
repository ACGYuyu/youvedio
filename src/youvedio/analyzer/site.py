"""AI site analyzer — determines if a URL is a relevant torrent site."""

from __future__ import annotations

import json
import logging
import re

import httpx

from youvedio.config import settings

logger = logging.getLogger(__name__)

ANALYSIS_PROMPT = (
    "You are a site classification assistant for a torrent search engine. "
    "Given the homepage HTML content of a website, determine if it is a "
    "torrent/magnet/subs download site for anime, TV shows, or movies.\n\n"
    "Return ONLY a JSON object with these fields:\n"
    "- 'is_torrent_site': true or false\n"
    "- 'confidence': float between 0 and 1\n"
    "- 'reason': short explanation (max 100 chars)\n\n"
    "Torrent sites typically have: magnet links, torrent files, seed/leech counts, "
    "anime titles with episode numbers, file sizes, or category lists like "
    "'Anime', 'TV Series', 'Movies'.\n\n"
    "Do not add explanations or markdown outside the JSON."
)


def analyze_url(url: str) -> dict:
    """Fetch a URL and analyze if it's a relevant torrent site.

    Returns dict with keys: url, domain, is_torrent_site, confidence, reason.
    """
    from urllib.parse import urlparse

    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path.split("/")[0]
    domain = re.sub(r"^www\d?\.", "", domain)

    # Fetch page
    content = _fetch_text(url)
    if not content:
        return {
            "url": url,
            "domain": domain,
            "is_torrent_site": False,
            "confidence": 0.0,
            "reason": "Failed to fetch page",
        }

    # Quick keyword check before AI call (cheap filter)
    quick = _quick_check(domain, content)
    if quick is not None:
        return {
            "url": url,
            "domain": domain,
            "is_torrent_site": quick[0],
            "confidence": quick[1],
            "reason": quick[2],
        }

    # AI analysis if API key is configured
    if not settings.deepseek_api_key:
        return {
            "url": url,
            "domain": domain,
            "is_torrent_site": False,
            "confidence": 0.0,
            "reason": "No AI API key configured",
        }

    return _ai_analyze(url, domain, content)


def _fetch_text(url: str) -> str | None:
    """Fetch a page and return visible text content."""
    try:
        from scrapling.fetchers import Fetcher

        resp = Fetcher.get(
            url,
            stealthy_headers=True,
            timeout=settings.crawler_timeout,
            impersonate="chrome",
        )
        # Extract text content (strip HTML tags)
        from scrapling.parser import Selector

        doc = Selector(resp.text)
        full_text = " ".join(doc.css("body *::text").getall())
        return full_text[:8000]  # limit token usage
    except Exception as e:
        logger.debug("Failed to fetch %s: %s", url, e)
        return None


def _quick_check(domain: str, text: str) -> tuple[bool, float, str] | None:
    """Quick keyword-based check before AI call."""
    lower = text.lower()
    domain_lower = domain.lower()

    # Torrent-related keywords
    torrent_keywords = [
        "magnet",
        "torrent",
        "种子",
        "btih",
        "info_hash",
        "seeders",
        "leechers",
        "peers",
    ]
    torrent_count = sum(1 for kw in torrent_keywords if kw in lower)

    # Domain-based hints
    domain_hints = [
        "torrent",
        "nyaa",
        "sukan",
        "anime",
        "subs",
        "magnet",
        "dmhy",
        "mikan",
        "btdb",
        "tokyotosho",
    ]
    domain_match = any(hint in domain_lower for hint in domain_hints)

    # Check for {domain} torrent search results
    if torrent_count >= 2 and domain_match:
        return True, 0.85, "Keywords + domain match"
    if torrent_count >= 4:
        return True, 0.70, "Strong keyword match"
    if domain_match and torrent_count >= 1:
        return True, 0.60, "Domain hint + keyword"

    return None  # needs AI analysis


def _ai_analyze(url: str, domain: str, content: str) -> dict:
    """Use DeepSeek to analyze page content."""
    try:
        result = _call_ai_api(content)
        if result:
            is_torrent = result.get("is_torrent_site", False)
            confidence = result.get("confidence", 0.0)
            reason = result.get("reason", "AI analysis")
            return {
                "url": url,
                "domain": domain,
                "is_torrent_site": bool(is_torrent),
                "confidence": float(confidence),
                "reason": str(reason),
            }
    except Exception as e:
        logger.warning("AI analysis failed for %s: %s", url, e)

    return {
        "url": url,
        "domain": domain,
        "is_torrent_site": False,
        "confidence": 0.0,
        "reason": "AI analysis failed",
    }


def _call_ai_api(content: str) -> dict | None:
    """Call DeepSeek API for site analysis."""
    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key}",
        "Content-Type": "application/json",
    }
    # Truncate content to avoid token limits
    truncated = content[:4000]
    payload = {
        "model": settings.deepseek_model,
        "messages": [
            {"role": "system", "content": ANALYSIS_PROMPT},
            {"role": "user", "content": truncated},
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

    # Try JSON parse
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Fallback: extract JSON block
    m = re.search(r"\{[^}]+\}", content, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass

    return None


def batch_analyze(urls: list[str]) -> list[dict]:
    """Analyze multiple URLs and return relevant ones."""
    results = [analyze_url(url) for url in urls]
    results.sort(key=lambda r: r.get("confidence", 0), reverse=True)
    return results
