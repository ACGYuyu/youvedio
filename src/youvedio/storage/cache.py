"""Search result cache with TTL expiration."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

_CACHE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "cache"
_DEFAULT_TTL = 600  # 10 minutes


def _key_path(key: str) -> Path:
    """Generate a filesystem-safe cache file path from a key string."""
    h = hashlib.md5(key.encode("utf-8")).hexdigest()
    return _CACHE_DIR / f"{h}.json"


def get(key: str, ttl: int = _DEFAULT_TTL) -> dict | None:
    """Read cached data for a key. Returns None if missing or expired."""
    path = _key_path(key)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        age = time.time() - data.get("_cached_at", 0)
        if age > ttl:
            path.unlink(missing_ok=True)
            return None
        return data.get("payload")
    except Exception:
        path.unlink(missing_ok=True)
        return None


def set(key: str, payload: dict) -> None:
    """Write payload to cache."""
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    data = {"_cached_at": time.time(), "payload": payload}
    path = _key_path(key)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def clear(ttl: int = _DEFAULT_TTL) -> int:
    """Remove all expired cache entries. Returns count of removed files."""
    if not _CACHE_DIR.exists():
        return 0
    now = time.time()
    count = 0
    for f in _CACHE_DIR.iterdir():
        if f.suffix != ".json":
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if now - data.get("_cached_at", 0) > ttl:
                f.unlink()
                count += 1
        except Exception:
            f.unlink()
            count += 1
    return count
