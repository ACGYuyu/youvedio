"""Application configuration via .env file and environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv


@dataclass
class Settings:
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    crawler_timeout: int = 10
    crawler_max_concurrent: int = 5
    http_proxy: str = ""
    https_proxy: str = ""
    _extra: dict[str, str] = field(default_factory=dict, repr=False)

    @classmethod
    def load(cls) -> Settings:
        load_dotenv()
        return cls(
            server_host=os.getenv("SERVER_HOST", "0.0.0.0"),
            server_port=int(os.getenv("SERVER_PORT", "8000")),
            crawler_timeout=int(os.getenv("CRAWLER_TIMEOUT", "10")),
            crawler_max_concurrent=int(os.getenv("CRAWLER_MAX_CONCURRENT", "5")),
            http_proxy=os.getenv("HTTP_PROXY", ""),
            https_proxy=os.getenv("HTTPS_PROXY", ""),
        )

    def apply_proxy(self) -> None:
        if self.http_proxy:
            os.environ["HTTP_PROXY"] = self.http_proxy
            os.environ["HTTPS_PROXY"] = self.https_proxy or self.http_proxy


settings = Settings.load()
