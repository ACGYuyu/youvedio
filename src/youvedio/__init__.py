"""YouVedio — 多语言种子/磁力搜索引擎."""

import logging


def _quiet_loggers() -> None:
    for name in (
        "scrapling",
        "scrapling.fetchers",
        "scrapling.parser",
        "scrapling.core",
        "scrapling.engines",
        "scrapling.engines.toolbelt",
        "httpx",
        "httpx._client",
        "curl_cffi",
        "playwright",
    ):
        logging.getLogger(name).setLevel(logging.WARNING)


_quiet_loggers()
