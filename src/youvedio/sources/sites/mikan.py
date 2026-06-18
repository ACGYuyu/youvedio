"""Mikanani (蜜柑计划) torrent site parser."""

from youvedio.models import TorrentResult
from youvedio.sources.sites.base import SiteParser


class MikanParser(SiteParser):
    """Parser for 蜜柑计划 - Chinese anime torrent site."""

    name = "mikanani.me"
    base_url = "https://mikanani.me"
    lang = "zh"

    def search_url(self, keyword: str) -> str:
        return f"{self.base_url}/Search/Results?searchStr={keyword}"

    def parse(self, html: str, source: str | None = None) -> list[TorrentResult]:
        from scrapling.parser import Selector

        doc = Selector(html)
        results: list[TorrentResult] = []
        source = source or self.name

        for row in doc.css("table > tbody > tr"):
            try:
                title = self.css_text(row, "td:nth-child(2) a::text")
                if not title:
                    continue

                page_url = self.extract_page_url(self.css_attr(row, "td:nth-child(2) a", "href"))
                magnet = self.css_attr(row, "a[href^='magnet:']", "href")
                if not magnet:
                    for a in row.css("a.ka[href]"):
                        h = self.css_attr(a, "", "href")
                        if h.startswith("magnet:"):
                            magnet = h
                            break

                size = self.normalize_size(self.css_text(row, "td:nth-child(4)::text"))
                info_hash = self.extract_info_hash(magnet)

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
