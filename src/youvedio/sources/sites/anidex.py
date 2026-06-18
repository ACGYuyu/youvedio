"""AniDEX torrent site parser."""

from youvedio.models import TorrentResult
from youvedio.sources.sites.base import SiteParser


class AnidexParser(SiteParser):
    """Parser for AniDEX.info - multilingual anime torrents."""

    name = "anidex.info"
    base_url = "https://anidex.info"
    lang = "en"

    def search_url(self, keyword: str) -> str:
        return f"{self.base_url}/?s={keyword}"

    def parse(self, html: str, source: str | None = None) -> list[TorrentResult]:
        from scrapling.parser import Selector

        doc = Selector(html)
        results: list[TorrentResult] = []
        source = source or self.name

        for row in doc.css("table > tbody > tr"):
            try:
                title = self.css_text(row, "td:nth-child(3) a::text")
                if not title:
                    continue

                page_path = self.css_attr(row, "td:nth-child(3) a", "href")
                if page_path.startswith("/"):
                    page_url = f"https://anidex.info{page_path}"
                else:
                    page_url = page_path

                magnet = self.css_attr(row, "a[href^='magnet:']", "href")
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
