"""AI-powered result classifier — organizes torrents by subgroup, season, quality."""

from __future__ import annotations

import json
import logging
import re

import httpx

from youvedio.config import settings
from youvedio.models import TorrentResult

logger = logging.getLogger(__name__)

_CLASSIFY_PROMPT = (
    "You are a torrent classification assistant. Given a search query "
    "and a list of torrent items, organize them by:\n\n"
    "1. Subtitle group (the name in [brackets] at the start of the title, "
    'or "unknown" if none)\n'
    "2. Season number (newest season first)\n"
    "3. Quality (4K > 2160p > 1080p > 720p > 480p > unknown)\n\n"
    "Return ONLY a JSON object with this exact structure:\n"
    "{\n"
    '  "groups": [\n'
    "    {\n"
    '      "subgroup": "GroupName",\n'
    '      "seasons": [\n'
    "        {\n"
    '          "season": 4,\n'
    '          "qualities": [\n'
    '            {"quality": "4K", "item_indices": [0, 5]},\n'
    '            {"quality": "1080P", "item_indices": [1, 3]}\n'
    "          ]\n"
    "        }\n"
    "      ]\n"
    "    }\n"
    "  ],\n"
    '  "unclassified_indices": []\n'
    "}\n\n"
    'Each item is numbered "item N:". Use N as item_indices.\n'
    "Quality values MUST be one of: 4K, 2160P, 1080P, 720P, 480P, "
    '360P, or "unknown".\n'
    "Do NOT include explanations outside the JSON."
)


def ai_classify_results(results: list[TorrentResult], keyword: str) -> dict | None:
    if not settings.deepseek_api_key:
        return None

    items_str = "\n".join(f"item {i}: {r.title[:150]}" for i, r in enumerate(results[:100]))
    if len(results) > 100:
        items_str += f"\n... and {len(results) - 100} more items"

    prompt = f"Search query: {keyword}\n\nItems:\n{items_str}"

    try:
        response = _call_ai(prompt)
        if response and "groups" in response:
            return response
    except Exception as e:
        logger.warning("AI classification failed: %s", e)

    return None


def _call_ai(prompt: str) -> dict | None:
    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.deepseek_model,
        "messages": [
            {"role": "system", "content": _CLASSIFY_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.05,
        "max_tokens": 2048,
    }

    with httpx.Client(timeout=30.0) as client:
        resp = client.post(
            f"{settings.deepseek_base_url.rstrip('/')}/chat/completions",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        body = resp.json()
        content = body["choices"][0]["message"]["content"]

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    m = re.search(r"\{.*\}", content, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass

    return None


def _to_dict(r: TorrentResult) -> dict:
    return {
        "source": r.source,
        "title": r.title,
        "magnet": r.magnet,
        "info_hash": r.info_hash,
        "size": r.size or "",
        "seeders": r.seeders,
        "leechers": r.leechers,
        "season": r.season,
        "episode": r.episode,
        "quality": r.quality or "",
        "source_type": r.source_type or "",
        "subgroup": r.subgroup or "",
        "page_url": r.page_url or "",
    }


def apply_ai_classification(results: list[TorrentResult], ai_data: dict) -> dict:
    output: dict = {}
    unclassified_keys: set[int] = set()

    for group in ai_data.get("groups", []):
        sg = group.get("subgroup", "_unknown")
        if sg not in output:
            output[sg] = {}

        for season_entry in group.get("seasons", []):
            sn = season_entry.get("season", 0)
            sk = f"S{sn:02d}" if sn else "_unclassified"
            if sk not in output[sg]:
                output[sg][sk] = {}

            for qual_entry in season_entry.get("qualities", []):
                q = qual_entry.get("quality", "Unknown").upper()
                indices = qual_entry.get("item_indices", [])
                items = []
                for idx in indices:
                    if 0 <= idx < len(results):
                        items.append(_to_dict(results[idx]))
                        unclassified_keys.add(idx)
                if items:
                    output[sg][sk][q] = items

    unclass_items = [_to_dict(r) for i, r in enumerate(results) if i not in unclassified_keys]
    if unclass_items:
        output.setdefault("_unknown", {}).setdefault("_unclassified", {})["All"] = unclass_items

    return output
