"""Application configuration via .env file and environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv


@dataclass
class Settings:
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    crawler_timeout: int = 30
    crawler_max_concurrent: int = 5
    _extra: dict[str, str] = field(default_factory=dict, repr=False)

    @classmethod
    def from_env(cls) -> Settings:
        load_dotenv()
        return cls(
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
            deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            server_host=os.getenv("SERVER_HOST", "0.0.0.0"),
            server_port=int(os.getenv("SERVER_PORT", "8000")),
            crawler_timeout=int(os.getenv("CRAWLER_TIMEOUT", "30")),
            crawler_max_concurrent=int(os.getenv("CRAWLER_MAX_CONCURRENT", "5")),
        )


settings = Settings.from_env()
