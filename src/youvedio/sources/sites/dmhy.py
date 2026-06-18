"""Dmhy (动漫花园) torrent site parser."""

from youvedio.models import TorrentResult
from youvedio.sources.sites.base import SiteParser


class DmhyParser(SiteParser):
    """Parser for 动漫花园 - Chinese anime torrent site."""

    name = "dmhy.org"
    base_url = "https://share.dmhy.org"
    lang = "zh"

    def search_url(self, keyword: str) -> str:
        return f"{self.base_url}/topics/list?keyword={keyword}"

    def parse(self, html: str, source: str | None = None) -> list[TorrentResult]:
        from scrapling.parser import Selector

        doc = Selector(html)
        results: list[TorrentResult] = []
        source = source or self.name

        for row in doc.css("table > tbody > tr"):
            try:
                title = self.css_text(row, "td:nth-child(3) a:last-child::text")
                if not title:
                    continue

                page_url = self.extract_page_url(
                    self.css_attr(row, "td:nth-child(3) a:last-child", "href")
                )
                magnet = self.css_attr(row, "td:nth-child(4) a[href^='magnet:']", "href")
                size = self.normalize_size(self.css_text(row, "td:nth-child(5)::text"))
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
