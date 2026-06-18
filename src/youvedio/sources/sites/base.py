"""Base class for torrent site parsers."""

from abc import ABC, abstractmethod

from scrapling.parser import Selector

from youvedio.config import settings
from youvedio.models import TorrentResult


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

    def fetch(self, keyword: str) -> list[TorrentResult]:
        """Fetch and parse search results from the site."""
        from scrapling.fetchers import Fetcher

        url = self.search_url(keyword)
        try:
            resp = Fetcher.get(
                url,
                stealthy_headers=True,
                timeout=settings.crawler_timeout,
                impersonate="chrome",
            )
            return self.parse(resp.text, source=self.name)
        except Exception:
            return []

    def css_text(self, el: Selector, css: str) -> str:
        """Extract text via CSS selector, returning empty string on failure."""
        handler = el.css(css)
        if handler is None:
            return ""
        val = handler.get()
        return str(val) if val is not None else ""

    def css_attr(self, el: Selector, css: str, attr: str) -> str:
        """Extract attribute via CSS selector."""
        handler = el.css(f"{css}::{attr}")
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
