"""ACG.RIP torrent site parser."""

from youvedio.models import TorrentResult
from youvedio.sources.sites.base import SiteParser


class AcgRipParser(SiteParser):
    """Parser for ACG.RIP - Chinese anime torrent site."""

    name = "acg.rip"
    base_url = "https://acg.rip"
    lang = "zh"

    def search_url(self, keyword: str) -> str:
        return f"{self.base_url}/?term={keyword}"

    def parse(self, html: str, source: str | None = None) -> list[TorrentResult]:
        from scrapling.parser import Selector

        doc = Selector(html)
        results: list[TorrentResult] = []
        source = source or self.name

        for row in doc.css("table.table-hover.table-condensed tr"):
            try:
                tds = row.css("td")
                if len(tds) < 4:
                    continue

                title_el = row.css("td:nth-child(2) a:last-child")
                raw = title_el.css("::text").get()
                title = str(raw).strip() if raw else ""
                if not title:
                    continue
                if len(title) < 3:
                    continue

                page_url = self.extract_page_url(
                    self.css_attr(row, "td:nth-child(2) a:last-child", "href")
                )

                magnet = self.css_attr(row, "td:nth-child(3) a", "href")
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
