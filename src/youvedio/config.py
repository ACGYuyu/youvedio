"""Application configuration — .env + data/settings.json + runtime."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_SETTINGS_FILE = _DATA_DIR / "settings.json"


@dataclass
class Settings:
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    crawler_timeout: int = 30
    crawler_max_concurrent: int = 3
    proxy_enabled: bool = False
    http_proxy: str = ""
    https_proxy: str = ""
    _extra: dict[str, str] = field(default_factory=dict, repr=False)

    @classmethod
    def load(cls) -> Settings:
        """Load: runtime file → .env → defaults."""
        load_dotenv()
        s = cls(
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
            deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            server_host=os.getenv("SERVER_HOST", "0.0.0.0"),
            server_port=int(os.getenv("SERVER_PORT", "8000")),
            crawler_timeout=int(os.getenv("CRAWLER_TIMEOUT", "30")),
            crawler_max_concurrent=int(os.getenv("CRAWLER_MAX_CONCURRENT", "3")),
            proxy_enabled=os.getenv("PROXY_ENABLED", "").lower() in ("1", "true"),
            http_proxy=os.getenv("HTTP_PROXY", ""),
            https_proxy=os.getenv("HTTPS_PROXY", ""),
        )
        # Override with persisted settings
        if _SETTINGS_FILE.exists():
            try:
                data = json.loads(_SETTINGS_FILE.read_text(encoding="utf-8"))
                for k, v in data.items():
                    if hasattr(s, k) and k != "_extra":
                        setattr(s, k, v)
            except Exception:
                pass
        return s

    def save(self) -> None:
        """Persist runtime settings to data/settings.json."""
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "deepseek_api_key": self.deepseek_api_key,
            "deepseek_base_url": self.deepseek_base_url,
            "deepseek_model": self.deepseek_model,
            "proxy_enabled": self.proxy_enabled,
            "http_proxy": self.http_proxy,
            "https_proxy": self.https_proxy,
        }
        _SETTINGS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def update(self, **kwargs) -> None:
        """Update fields at runtime (skip None/empty values unless explicit)."""
        for k, v in kwargs.items():
            if not hasattr(self, k) or k == "_extra":
                continue
            if isinstance(getattr(self, k), bool) or v is not None:
                setattr(self, k, v)
        self.save()

    def apply_proxy(self) -> None:
        """Set proxy environment variables for curl_cffi/httpx.

        Only sets proxy when proxy_enabled is True; never removes existing
        proxy configuration to avoid breaking system proxy settings.
        """
        if self.proxy_enabled and self.http_proxy:
            os.environ["HTTP_PROXY"] = self.http_proxy
            os.environ["HTTPS_PROXY"] = self.https_proxy or self.http_proxy
        # Do NOT unset proxy when disabled — leave system proxy alone

    @staticmethod
    def get_data_dir() -> Path:
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        return _DATA_DIR

    def to_dict(self) -> dict:
        """Public settings — exclude internal/server fields."""
        return {
            "deepseek_api_key": bool(self.deepseek_api_key),
            "deepseek_base_url": self.deepseek_base_url,
            "deepseek_model": self.deepseek_model,
            "proxy_enabled": self.proxy_enabled,
            "http_proxy": self.http_proxy,
            "https_proxy": self.https_proxy,
        }

    def to_full_dict(self) -> dict:
        return {
            "deepseek_api_key": self.deepseek_api_key,
            "deepseek_base_url": self.deepseek_base_url,
            "deepseek_model": self.deepseek_model,
            "proxy_enabled": self.proxy_enabled,
            "http_proxy": self.http_proxy,
            "https_proxy": self.https_proxy,
        }


settings = Settings.load()
