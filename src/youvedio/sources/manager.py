"""Central source manager that registers and dispatches site parsers."""

from __future__ import annotations

import json
from pathlib import Path

from youvedio.models import TorrentResult
from youvedio.sources.sites.base import SiteParser

_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"
_SOURCES_FILE = Path(__file__).resolve().parent.parent.parent.parent / "sources.json"


def _load_parsers() -> dict[str, SiteParser]:
    """Auto-discover and instantiate all site parsers."""
    import importlib
    import pkgutil

    parsers: dict[str, SiteParser] = {}
    pkg_path = Path(__file__).parent / "sites"
    for mod_info in pkgutil.iter_modules([str(pkg_path)]):
        if mod_info.name == "base":
            continue
        mod = importlib.import_module(f"youvedio.sources.sites.{mod_info.name}")
        for attr_name in dir(mod):
            attr = getattr(mod, attr_name)
            if isinstance(attr, type) and issubclass(attr, SiteParser) and attr is not SiteParser:
                instance = attr()
                parsers[instance.name] = instance
    return parsers


class SourceManager:
    """Manages known torrent sites and their parsers."""

    def __init__(self) -> None:
        self._parsers = _load_parsers()
        self._config = self._load_config()

    def _load_config(self) -> dict[str, dict]:
        """Load source configuration from sources.json."""
        if _SOURCES_FILE.exists():
            raw = json.loads(_SOURCES_FILE.read_text(encoding="utf-8"))
            return {entry["name"]: entry for entry in raw}
        return {}

    @property
    def enabled_parsers(self) -> dict[str, SiteParser]:
        """Return parsers for enabled sources."""
        enabled: dict[str, SiteParser] = {}
        for name, parser in self._parsers.items():
            cfg = self._config.get(name, {})
            if cfg.get("enabled", parser.enabled):
                enabled[name] = parser
        return enabled

    @property
    def all_parsers(self) -> dict[str, SiteParser]:
        return dict(self._parsers)

    def search_all(self, keyword: str, limit: int = 50) -> list[TorrentResult]:
        """Search all enabled sites in parallel."""
        import concurrent.futures

        results: list[TorrentResult] = []
        parsers = list(self.enabled_parsers.values())

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
            fut_to_parser = {pool.submit(p.fetch, keyword): p for p in parsers}
            for fut in concurrent.futures.as_completed(fut_to_parser):
                try:
                    items = fut.result()
                    results.extend(items)
                except Exception:
                    continue

        results.sort(key=lambda r: r.seeders or 0, reverse=True)
        if limit and len(results) > limit:
            results = results[:limit]
        return results

    def search_site(self, name: str, keyword: str) -> list[TorrentResult]:
        """Search a specific site by name."""
        parser = self._parsers.get(name)
        if not parser:
            return []
        cfg = self._config.get(name, {})
        if not cfg.get("enabled", parser.enabled):
            return []
        return parser.fetch(keyword)

    def get_parser(self, name: str) -> SiteParser | None:
        return self._parsers.get(name)


_instance: SourceManager | None = None


def get_source_manager() -> SourceManager:
    global _instance
    if _instance is None:
        _instance = SourceManager()
    return _instance
