"""Base class for torrent site parsers."""

import logging
import os
from abc import ABC, abstractmethod

from scrapling.parser import Selector

from youvedio.config import settings
from youvedio.models import TorrentResult

# Silence INFO noise from scrapling's parser internals
logging.getLogger("scrapling").setLevel(logging.WARNING)
logging.getLogger("scrapling.parser").setLevel(logging.WARNING)


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

    def fetch(self, keyword: str) -> list[TorrentResult]:
        """Fetch and parse search results from the site.

        Uses curl_cffi (TLS fingerprint) with httpx fallback.
        """
        url = self.search_url(keyword)
        proxy = self._proxies()

        try:
            from curl_cffi import requests as curl_requests

            sess_kw: dict = {
                "impersonate": "chrome",
                "timeout": settings.crawler_timeout,
            }
            if proxy:
                sess_kw["proxies"] = proxy
            with curl_requests.Session(**sess_kw) as s:
                resp = s.get(url, allow_redirects=True)
                if resp.status_code == 200:
                    return self.parse(resp.text, source=self.name)
        except Exception:
            pass

        try:
            import httpx

            client_kw: dict = {
                "timeout": settings.crawler_timeout,
                "follow_redirects": True,
            }
            if proxy:
                client_kw["proxy"] = proxy.get("http", proxy.get("https"))
            with httpx.Client(**client_kw) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    return self.parse(resp.text, source=self.name)
        except Exception:
            pass

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
