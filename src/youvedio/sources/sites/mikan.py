"""Mikanani (蜜柑计划) torrent site parser."""

from youvedio.models import TorrentResult
from youvedio.sources.sites.base import SiteParser


class MikanParser(SiteParser):
    """Parser for 蜜柑计划 - Chinese anime torrent site."""

    name = "mikanani.me"
    base_url = "https://mikanani.me"
    lang = "zh"

    def search_url(self, keyword: str) -> str:
        return f"{self.base_url}/Home/Search?searchStr={keyword}"

    def parse(self, html: str, source: str | None = None) -> list[TorrentResult]:
        from scrapling.parser import Selector

        doc = Selector(html)
        results: list[TorrentResult] = []
        source = source or self.name

        for row in doc.css("tr.js-search-results-row"):
            try:
                magnet = row.css("input.js-episode-select::attr(data-magnet)").get() or ""
                if not magnet:
                    continue

                title = self.css_text(row, "td:nth-child(2) a:first-child::text")
                if not title:
                    continue

                size = self.normalize_size(self.css_text(row, "td:nth-child(3)::text"))
                info_hash = self.extract_info_hash(magnet)
                page_path = self.css_attr(row, "td:nth-child(2) a:first-child", "href")
                page_url = self.extract_page_url(page_path) if page_path else ""

                results.append(
                    TorrentResult.create(
                        source=source,
                        title=title,
                        magnet=magnet,
                        info_hash=info_hash,
                        size=size,
                        page_url=page_url,
                    )
                )
            except Exception:
                continue

        return results
