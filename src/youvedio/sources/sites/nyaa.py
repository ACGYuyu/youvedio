"""Nyaa.si torrent site parser."""

from youvedio.models import TorrentResult
from youvedio.sources.sites.base import SiteParser


class NyaaParser(SiteParser):
    """Parser for Nyaa.si - primarily anime torrents."""

    name = "nyaa.si"
    base_url = "https://nyaa.si"
    lang = "en"

    def search_url(self, keyword: str) -> str:
        params = f"?f=0&c=0_0&q={keyword}"
        return f"{self.base_url}/{params}"

    def parse(self, html: str, source: str | None = None) -> list[TorrentResult]:
        from scrapling.parser import Selector

        doc = Selector(html)
        results: list[TorrentResult] = []
        source = source or self.name

        for row in doc.css("table.torrent-list > tbody > tr"):
            try:
                title = self.css_text(row, "td:nth-child(2) a:last-child::text")
                if not title:
                    continue

                magnet = self.css_attr(row, "a[href^='magnet:']", "href")
                page_url = self.extract_page_url(
                    self.css_attr(row, "td:nth-child(2) a:last-child", "href")
                )
                size = self.normalize_size(self.css_text(row, "td:nth-child(4)::text"))
                seeders = self.safe_int(self.css_text(row, "td:nth-child(6)::text"))
                leechers = self.safe_int(self.css_text(row, "td:nth-child(7)::text"))
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
