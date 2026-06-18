---
name: youvedio-torrent-search
description: >
  Search torrent/magnet sites for anime and video content via the YouVedio MCP server.
  Use when the user wants to watch, download, or find torrent/magnet links for a show.
  One search covers all seasons/qualities — do NOT re-search for specific qualities.
license: MIT
compatibility: opencode
---

## When to use

When the user asks to watch, download, or find torrents for an anime or show.

## Key rule — one search is enough

**Search once with the show name. Do NOT re-search for specific qualities, seasons, or batch.** The returned `quality_summary` already tells you everything available.

## Search strategy

1. Call `search_torrents` with the show's full name once
2. Read `quality_summary` to see what exists (seasons, qualities, subgroups)
3. From `quality_summary` you can tell:
   - `has_batch=true` → there IS a batch/complete pack
   - `has_single_episodes=true` → only single episodes exist
   - `subgroups` list tells you which fansub groups have releases
4. Navigate `seasons[S04][1080P]` for the actual items
5. **Check `_unclassified`** for movies, OVAs, SPs — they have no season numbers
   but may contain 4K/2160P content the user wants
6. If the user wants batch but `has_batch=false`, it means ongoing series — list single episodes instead

## Formatting the response

```
[SubGroup] → Season X → Quality (count)

If the user asks for a specific quality that exists, show only that quality.
If batch exists, give batch magnet. If only single episodes exist, list them all.
Recommend highest-seeded option.

Batch vs single episodes:
- item.episode === null → this is a batch/complete pack
- item.episode !== null → this is a single episode
```

## Common abbreviations (resolve yourself)

| Abbr | Full Title |
|------|-----------|
| RE0, Re0 | Re:Zero kara Hajimeru Isekai Seikatsu |
| S1 | Sonny Boy |
| MHA | My Hero Academia / Boku no Hero Academia |
| AOT | Attack on Titan / Shingeki no Kyojin |
| MT | Mushoku Tensei |
| OPM | One Punch Man |
