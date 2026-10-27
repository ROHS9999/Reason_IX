"""Web search for claim verification. Tavily if TAVILY_API_KEY is set, otherwise the keyless `ddgs` package.
We only ever read the SNIPPETS the search engine returns - we never fetch result URLs ourselves (no SSRF risk)."""
import requests

import config


class WebSearchUnavailable(Exception):
    pass


def search(query: str, n: int = config.WEB_RESULTS) -> list:
    """Returns [{title, url, snippet}, ...]."""
    return _tavily(query, n) if config.TAVILY_API_KEY else _ddgs(query, n)


def _tavily(query: str, n: int) -> list:
    try:
        r = requests.post("https://api.tavily.com/search",
                          json={"query": query, "max_results": n, "search_depth": "basic"},
                          headers={"Authorization": f"Bearer {config.TAVILY_API_KEY}"}, timeout=15)
        r.raise_for_status()
        items = r.json().get("results", [])
    except Exception as e:  # noqa: BLE001
        raise WebSearchUnavailable(f"Web search failed: {e}")
    return [{"title": x.get("title", ""), "url": x.get("url", ""), "snippet": x.get("content", "")} for x in items][:n]


def _ddgs(query: str, n: int) -> list:
    try:
        from ddgs import DDGS
    except ImportError:
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            raise WebSearchUnavailable("No web search provider: run `pip install ddgs` or set TAVILY_API_KEY in .env")
    try:
        items = DDGS().text(query, max_results=n) or []
    except Exception as e:  # noqa: BLE001
        raise WebSearchUnavailable(f"Web search failed: {e}")
    return [{"title": x.get("title", ""), "url": x.get("href", ""), "snippet": x.get("body", "")} for x in items][:n]
