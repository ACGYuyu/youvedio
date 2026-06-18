"""TokyoTosho torrent site parser — uses RSS feed (search.php returns 500)."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

from youvedio.config import settings
from youvedio.models import TorrentResult
from youvedio.sources.sites.base import SiteParser


class TokyoToshoParser(SiteParser):
    """Parser for TokyoTosho.info - anime torrents."""

    name = "tokyotosho.info"
    base_url = "https://www.tokyotosho.info"
    lang = "en"

    def search_url(self, keyword: str) -> str:
        return f"{self.base_url}/rss.php?terms={keyword}"

    def parse(self, html: str, source: str | None = None) -> list[TorrentResult]:
        results: list[TorrentResult] = []
        source = source or self.name
        try:
            root = ET.fromstring(html)
        except ET.ParseError:
            return results

        for item in root.iter("item"):
            try:
                title_el = item.find("title")
                if title_el is None or not title_el.text:
                    continue
                title = title_el.text.strip()
                if not title:
                    continue

                desc_el = item.find("description")
                desc = (desc_el.text or "") if desc_el is not None else ""

                magnet = self._extract_from_desc(desc, r'href="(magnet:\?xt=[^"]+)"')
                page_url = self._extract_from_desc(
                    desc, r'href="(https?://[^"]+/details\.php\?id=\d+)"'
                )

                size = self._extract_from_desc(desc, r"Size:\s*([^<]+)")
                seeders = 0
                leechers = 0
                info_hash = self.extract_info_hash(magnet)

                results.append(
                    TorrentResult.create(
                        source=source,
                        title=title,
                        magnet=magnet,
                        info_hash=info_hash,
                        size=size,
                        seeders=seeders,
                        leechers=leechers,
                        page_url=page_url,
                    )
                )
            except Exception:
                continue

        return results

    def fetch(self, keyword: str) -> list[TorrentResult]:
        """Try curl_cffi (TLS fingerprint) first, fallback to httpx."""
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
                ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                resp = client.get(url, headers={"User-Agent": ua})
                return self.parse(resp.text, source=self.name)
        except Exception:
            return []

    @staticmethod
    def _extract_from_desc(desc: str, pattern: str) -> str:
        m = re.search(pattern, desc)
        return m.group(1).strip() if m else ""
