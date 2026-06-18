"""Base class for torrent site parsers."""

import logging
import os
from abc import ABC, abstractmethod

from scrapling.parser import Selector

from youvedio.config import settings
from youvedio.models import TorrentResult

# Scrapling creates its own INFO handler — silence it after import
logging.getLogger("scrapling").setLevel(logging.WARNING)
for _name in (
    "scrapling.fetchers",
    "scrapling.parser",
    "scrapling.core",
    "scrapling.engines",
    "scrapling.engines.toolbelt",
):
    logging.getLogger(_name).setLevel(logging.WARNING)


class SiteParser(ABC):
    """Abstract base for all torrent site parsers."""

    name: str = ""
    base_url: str = ""
    lang: str = "en"
    enabled: bool = True

    def __init__(self) -> None:
        if not self.name:
            self.name = type(self).__name__.lower().replace("parser", "")

    @abstractmethod
    def search_url(self, keyword: str) -> str:
        """Build the search URL for a keyword."""

    @abstractmethod
    def parse(self, html: str, source: str | None = None) -> list[TorrentResult]:
        """Parse search results page HTML into TorrentResult list."""

    def _proxies(self) -> dict | None:
        """Return proxy dict: settings proxy > env var > None."""
        http = (
            settings.http_proxy
            or os.environ.get("HTTP_PROXY")
            or os.environ.get("http_proxy")
            or ""
        )
        https = (
            settings.https_proxy
            or os.environ.get("HTTPS_PROXY")
            or os.environ.get("https_proxy")
            or ""
        )
        if not http:
            return None
        return {"http": http, "https": https or http}

    @staticmethod
    def _cleanup_env_proxy() -> dict[str, str | None]:
        """Pop proxy env vars that Scrapling may read internally; return old values."""
        saved: dict[str, str | None] = {}
        for var in (
            "HTTP_PROXY",
            "HTTPS_PROXY",
            "http_proxy",
            "https_proxy",
            "ALL_PROXY",
            "all_proxy",
        ):
            saved[var] = os.environ.pop(var, None)
        return saved

    @staticmethod
    def _restore_env_proxy(saved: dict[str, str | None]) -> None:
        for var, val in saved.items():
            if val is not None:
                os.environ[var] = val
            else:
                os.environ.pop(var, None)

    def fetch(self, keyword: str) -> list[TorrentResult]:
        """Fetch and parse search results from the site."""
        from scrapling.fetchers import Fetcher

        url = self.search_url(keyword)
        try:
            kwargs: dict = {
                "stealthy_headers": True,
                "timeout": settings.crawler_timeout,
                "impersonate": "chrome",
            }
            proxy = self._proxies()
            saved = self._cleanup_env_proxy() if not proxy else None
            try:
                if proxy:
                    kwargs["proxies"] = proxy
                resp = Fetcher.get(url, **kwargs)
            finally:
                if saved is not None:
                    self._restore_env_proxy(saved)
            html = resp.body.decode(resp.encoding or "utf-8")
            return self.parse(html, source=self.name)
        except Exception:
            return []

    def css_text(self, el: Selector, css: str) -> str:
        """Extract text via CSS selector, returning empty string on failure."""
        handler = el.css(css)
        if handler is None:
            return ""
        val = handler.get()
        text = str(val).strip() if val is not None else ""
        return text

    def css_attr(self, el: Selector, css: str, attr: str) -> str:
        """Extract attribute via CSS selector."""
        handler = el.css(f"{css}::attr({attr})")
        if handler is None:
            return ""
        val = handler.get()
        return str(val) if val is not None else ""

    def normalize_size(self, size_text: str) -> str:
        """Clean and normalize size text."""
        return size_text.strip() if size_text else ""

    @staticmethod
    def safe_int(text: str | None) -> int:
        """Parse text to int, return 0 on failure."""
        if text:
            stripped = text.strip()
            if stripped.isdigit():
                return int(stripped)
        return 0

    @staticmethod
    def extract_info_hash(magnet: str) -> str:
        """Extract info hash from magnet URI."""
        import re

        m = re.search(r"btih:([a-fA-F0-9]+)", magnet)
        return m.group(1).lower() if m else ""

    def extract_page_url(self, path: str) -> str:
        """Build full page URL from a relative path."""
        if path.startswith("http"):
            return path
        base = self.base_url.rstrip("/")
        return f"{base}/{path.lstrip('/')}"
