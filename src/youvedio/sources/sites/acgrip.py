"""ACG.RIP torrent site parser."""

from youvedio.models import TorrentResult
from youvedio.sources.sites.base import SiteParser


class AcgRipParser(SiteParser):
    """Parser for ACG.RIP - Chinese anime torrent site."""

    name = "acg.rip"
    base_url = "https://acg.rip"
    lang = "zh"

    def search_url(self, keyword: str) -> str:
        return f"{self.base_url}/search/{keyword}"

    def parse(self, html: str, source: str | None = None) -> list[TorrentResult]:
        from scrapling.parser import Selector

        doc = Selector(html)
        results: list[TorrentResult] = []
        source = source or self.name

        for row in doc.css("table.ui.striped.table > tbody > tr"):
            try:
                title = self.css_text(row, "td:nth-child(2) a::text")
                if not title:
                    continue

                page_url = self.extract_page_url(self.css_attr(row, "td:nth-child(2) a", "href"))
                magnet = self.css_attr(row, "a[href^='magnet:']", "href")
                size = self.normalize_size(self.css_text(row, "td:nth-child(3)::text"))
                seeders = self.safe_int(self.css_text(row, "td:nth-child(4)::text"))
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
