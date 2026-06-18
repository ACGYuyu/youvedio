"""Crawler engine — concurrent site fetching with retry and progress."""

from __future__ import annotations

import concurrent.futures
import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from youvedio.crawler.classifier import classify
from youvedio.models import TorrentResult
from youvedio.sources.manager import SourceManager

logger = logging.getLogger(__name__)


@dataclass
class CrawlProgress:
    """Progress report and results for a crawl session."""

    total_sites: int = 0
    completed: int = 0
    success: int = 0
    failed: int = 0
    results_found: int = 0
    errors: list[str] = field(default_factory=list)
    results: list[TorrentResult] = field(default_factory=list)


class CrawlerEngine:
    """Central crawler with concurrent site fetching and retry."""

    def __init__(
        self,
        source_manager: SourceManager | None = None,
        max_concurrent: int = 5,
        retry_count: int = 1,
        retry_delay: float = 0.5,
    ) -> None:
        self.source_manager = source_manager or SourceManager()
        self.max_concurrent = max_concurrent
        self.retry_count = retry_count
        self.retry_delay = retry_delay

    def search(
        self,
        keyword: str,
        site_names: list[str] | None = None,
        on_progress: Callable[[str, str, int, int], None] | None = None,
    ) -> CrawlProgress:
        """Search all sites concurrently."""
        parsers = self.source_manager.enabled_parsers
        if site_names:
            parsers = {n: p for n, p in parsers.items() if n in site_names}

        progress = CrawlProgress(total_sites=len(parsers))
        all_results: list[TorrentResult] = []
        lock = threading.Lock()

        def _fetch_one(name: str, parser: object) -> tuple[str, list[TorrentResult]]:
            if on_progress:
                on_progress(name, "fetching", 0, 0)
            try:
                results = self._fetch_with_retry(parser, keyword)
                classified = [classify(r) for r in results]
                with lock:
                    all_results.extend(classified)
                if on_progress:
                    on_progress(name, "ok", 0, 0)
                return name, results
            except Exception as e:
                with lock:
                    progress.errors.append(f"{name}: {e}")
                if on_progress:
                    on_progress(name, "fail", 0, 0)
                return name, []

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_concurrent) as pool:
            futs = {pool.submit(_fetch_one, name, parser) for name, parser in parsers.items()}
            for fut in concurrent.futures.as_completed(futs):
                name, results = fut.result()
                with lock:
                    progress.completed += 1
                    if results:
                        progress.success += 1
                        progress.results_found += len(results)

        progress.results = list(all_results)
        progress.results_found = len(all_results)
        return progress

    def _fetch_with_retry(self, parser, keyword: str) -> list[TorrentResult]:
        last_error: Exception | None = None
        for attempt in range(self.retry_count + 1):
            try:
                return parser.fetch(keyword)
            except Exception as e:
                last_error = e
                if attempt < self.retry_count:
                    time.sleep(self.retry_delay * (2**attempt))
        if last_error:
            raise last_error
        return []


def search(keyword: str, **kwargs) -> CrawlProgress:
    """Convenience function: create engine and search."""
    engine = CrawlerEngine(**kwargs)
    return engine.search(keyword)
