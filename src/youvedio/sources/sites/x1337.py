"""1337x torrent site parser."""

from youvedio.config import settings
from youvedio.models import TorrentResult
from youvedio.sources.sites.base import SiteParser


class X1337Parser(SiteParser):
    """Parser for 1337x.to - general torrent site."""

    name = "1337x.to"
    base_url = "https://1337x.to"
    lang = "en"

    def search_url(self, keyword: str) -> str:
        return f"{self.base_url}/search/{keyword}/1/"

    def parse(self, html: str, source: str | None = None) -> list[TorrentResult]:
        from scrapling.parser import Selector

        doc = Selector(html)
        results: list[TorrentResult] = []
        source = source or self.name

        for row in doc.css("table.table-list > tbody > tr"):
            try:
                title = self.css_text(row, "td:nth-child(1) a:nth-child(2)::text")
                if not title:
                    title = self.css_text(row, "td:nth-child(1) a:last-child::text")
                if not title:
                    continue

                page_url = self.extract_page_url(
                    self.css_attr(row, "td:nth-child(1) a:last-child", "href")
                )
                seeders = self.safe_int(self.css_text(row, "td:nth-child(2)::text"))
                leechers = self.safe_int(self.css_text(row, "td:nth-child(3)::text"))
                size = self.normalize_size(self.css_text(row, "td:nth-child(4)::text"))

                results.append(
                    TorrentResult.create(
                        source=source,
                        title=title,
                        magnet="",
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
        """Override: 1337x often needs stealth fetching."""
        url = self.search_url(keyword)
        try:
            from scrapling.fetchers import StealthyFetcher

            kwargs: dict = {
                "headless": True,
                "timeout": settings.crawler_timeout,
            }
            proxy = self._proxies()
            if proxy:
                kwargs["proxies"] = proxy
            page = StealthyFetcher.fetch(url, **kwargs)
            return self.parse(page.text, source=self.name)
        except Exception:
            return super().fetch(keyword)
