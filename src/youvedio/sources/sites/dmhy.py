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
                title = self.css_text(row, "td:nth-child(2) a::text")
                if not title:
                    continue

                magnet = ""
                page_url = ""
                for a in row.css("td:last-child a[href]"):
                    href = self.css_attr(a, "", "href")
                    if href.startswith("magnet:"):
                        magnet = href
                    elif "dmhy.org" in href or "topics/view" in href:
                        page_url = href

                size = self.normalize_size(self.css_text(row, "td:nth-child(4)::text"))
                seeders = self.safe_int(self.css_text(row, "td:nth-child(5)::text"))
                info_hash = self.extract_info_hash(magnet)

                results.append(
                    TorrentResult.create(
                        source=source,
                        title=title,
                        magnet=magnet,
                        info_hash=info_hash,
                        size=size,
                        seeders=seeders,
                        page_url=page_url,
                    )
                )
            except Exception:
                continue

        return results
