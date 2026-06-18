"""TokyoTosho torrent site parser."""

from youvedio.models import TorrentResult
from youvedio.sources.sites.base import SiteParser


class TokyoToshoParser(SiteParser):
    """Parser for TokyoTosho.info - anime torrents."""

    name = "tokyotosho.info"
    base_url = "https://tokyotosho.info"
    lang = "en"

    def search_url(self, keyword: str) -> str:
        return f"{self.base_url}/search.php?search={keyword}"

    def parse(self, html: str, source: str | None = None) -> list[TorrentResult]:
        from scrapling.parser import Selector

        doc = Selector(html)
        results: list[TorrentResult] = []
        source = source or self.name

        for row in doc.css("div.list-topic"):
            try:
                title = self.css_text(row, "div.name a::text")
                if not title:
                    continue

                page_url = self.extract_page_url(self.css_attr(row, "div.name a", "href"))
                magnet = self.css_attr(row, "a[href^='magnet:']", "href")
                size = self.normalize_size(self.css_text(row, "span.size::text"))
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
