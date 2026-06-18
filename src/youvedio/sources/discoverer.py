"""Web search engine discoverer — find potential torrent sites."""

from __future__ import annotations

import logging
import re
from urllib.parse import urlparse

from youvedio.config import settings
from youvedio.translation import translate_query

logger = logging.getLogger(__name__)

# Known site domains to exclude from discovery results
_KNOWN_DOMAINS: set[str] = {
    "nyaa.si",
    "share.dmhy.org",
    "mikanani.me",
    "1337x.to",
    "acg.rip",
    "anidex.info",
    "tokyotosho.info",
    "nyaa.land",
    "sukebei.nyaa.si",
}

# Search engine URLs
_SEARCH_ENGINES: dict[str, str] = {
    "google": "https://www.google.com/search?q={q}&num=20",
    "bing": "https://www.bing.com/search?q={q}&count=20",
}


def _extract_domain(url: str) -> str:
    """Extract clean domain from a URL."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        # Remove www. prefix
        domain = re.sub(r"^www\d?\.", "", domain)
        # Remove path after first /
        domain = domain.split("/")[0]
        return domain.lower()
    except Exception:
        return ""


def _is_valid_candidate(url: str) -> bool:
    """Check if a URL is a valid candidate for a new torrent site."""
    domain = _extract_domain(url)
    if not domain:
        return False
    # Skip known search engines and common non-torrent sites
    skip_domains: set[str] = {
        "google.com",
        "bing.com",
        "youtube.com",
        "facebook.com",
        "twitter.com",
        "x.com",
        "reddit.com",
        "github.com",
        "wikipedia.org",
        "imdb.com",
        "amazon.com",
        "instagram.com",
    }
    if domain in skip_domains:
        return False
    # Skip IP addresses
    if re.match(r"^\d+\.\d+\.\d+\.\d+", domain):
        return False
    # Skip known sites
    if domain in _KNOWN_DOMAINS:
        return False
    # Must be a proper domain with dot
    return "." in domain


def _extract_google_links(html: str) -> list[str]:
    """Extract result links from Google search HTML."""
    urls: list[str] = []
    # Google uses <a href="/url?q=..."> format
    pattern = re.compile(r'<a[^>]*href\s*=\s*["\']/url\?q=([^"\'&]+)')
    for m in pattern.finditer(html):
        import urllib.parse

        decoded = urllib.parse.unquote(m.group(1))
        urls.append(decoded)
    return urls


def _extract_bing_links(html: str) -> list[str]:
    """Extract result links from Bing search HTML."""
    urls: list[str] = []
    pattern = re.compile(r'<a[^>]*href\s*=\s*["\'](https?://[^"\']+?)["\']')
    for m in pattern.finditer(html):
        url = m.group(1)
        # Skip Bing internal links
        if "bing.com" in url or "msn.com" in url:
            continue
        urls.append(url)
    return urls


def _remove_duplicates(urls: list[str]) -> list[str]:
    """Remove duplicate URLs and known sites."""
    seen: set[str] = set()
    result: list[str] = []
    for url in urls:
        domain = _extract_domain(url)
        if domain and domain not in seen and _is_valid_candidate(url):
            seen.add(domain)
            result.append(url)
    return result


def discover(
    keyword: str,
    engines: list[str] | None = None,
) -> list[dict[str, str]]:
    """Search for torrent sites related to a keyword.

    Returns list of dicts with 'url', 'domain', 'source' (search engine).
    """
    if not engines:
        engines = ["google"]

    # Translate keyword for multi-language search
    translations = translate_query(keyword)
    search_terms: list[str] = []
    for val in [keyword, translations.get("en", ""), translations.get("ja", "")]:
        if val and val not in search_terms:
            search_terms.append(val)

    candidates: list[dict[str, str]] = []
    seen_domains: set[str] = set()

    for engine_name in engines:
        template = _SEARCH_ENGINES.get(engine_name)
        if not template:
            continue

        for term in search_terms:
            search_query = f"{term} torrent magnet site"
            url = template.replace("{q}", search_query.replace(" ", "+"))

            try:
                from scrapling.fetchers import Fetcher

                resp = Fetcher.get(
                    url,
                    stealthy_headers=True,
                    timeout=settings.crawler_timeout,
                    impersonate="chrome",
                )

                if engine_name == "google":
                    links = _extract_google_links(resp.text)
                elif engine_name == "bing":
                    links = _extract_bing_links(resp.text)
                else:
                    continue

                for link in links:
                    domain = _extract_domain(link)
                    if domain and domain not in seen_domains and _is_valid_candidate(link):
                        seen_domains.add(domain)
                        candidates.append(
                            {
                                "url": link,
                                "domain": domain,
                                "source": engine_name,
                                "search_term": term,
                            }
                        )
            except Exception as e:
                logger.warning("Search engine '%s' failed: %s", engine_name, e)

    return candidates
