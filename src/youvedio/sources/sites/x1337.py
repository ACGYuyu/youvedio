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

    def parse_detail_page(self, html: str) -> str:
        """Extract magnet link from a torrent detail page."""
        from scrapling.parser import Selector

        doc = Selector(html)
        return self.css_attr(doc, "a[href^='magnet:']", "href")

    def fetch(self, keyword: str) -> list[TorrentResult]:
        """Override: 1337x often needs stealth fetching + follow detail for magnet."""
        url = self.search_url(keyword)
        try:
            from scrapling.fetchers import StealthyFetcher

            kwargs: dict = {
                "headless": True,
                "timeout": settings.crawler_timeout * 1000,
            }
            proxy = self._proxies()
            saved = self._cleanup_env_proxy() if not proxy else None
            if proxy:
                kwargs["proxies"] = proxy
            try:
                page = StealthyFetcher.fetch(url, **kwargs)
                results = self.parse(page.text, source=self.name)

                for r in results:
                    if r.page_url and not r.magnet:
                        try:
                            detail = StealthyFetcher.fetch(r.page_url, **kwargs)
                            magnet = self.parse_detail_page(detail.text)
                            if magnet:
                                r.magnet = magnet
                                r.info_hash = self.extract_info_hash(magnet)
                        except Exception:
                            continue
            finally:
                if saved is not None:
                    self._restore_env_proxy(saved)
            return results
        except Exception:
            return super().fetch(keyword)
