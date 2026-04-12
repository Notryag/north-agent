from __future__ import annotations

import re
from html import unescape
from urllib.parse import parse_qs, quote_plus, unquote, urlparse
from urllib.request import Request, urlopen

from langchain_core.tools import tool

SEARCH_ENDPOINT = "https://html.duckduckgo.com/html/?q={query}"
DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible; DeerFlowLite/0.1)"


def _fetch_search_html(query: str) -> str:
    request = Request(
        SEARCH_ENDPOINT.format(query=quote_plus(query)),
        headers={"User-Agent": DEFAULT_USER_AGENT},
    )
    with urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", errors="replace")


def _strip_tags(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value)
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _resolve_result_url(raw_url: str) -> str:
    candidate = unescape(raw_url).strip()
    if candidate.startswith("//"):
        candidate = f"https:{candidate}"
    parsed = urlparse(candidate)
    query = parse_qs(parsed.query)
    uddg = query.get("uddg")
    if uddg:
        return unquote(uddg[0])
    return candidate


def _parse_search_results(html: str, *, max_results: int) -> list[dict[str, str]]:
    blocks = re.split(r'<div class="result results_links.*?web-result\s*">', html, flags=re.IGNORECASE | re.DOTALL)[1:]
    results: list[dict[str, str]] = []

    for block in blocks:
        link_match = re.search(
            r'<a[^>]*class="result__a"[^>]*href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>',
            block,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if not link_match:
            continue

        snippet_match = re.search(
            r'<a[^>]*class="result__snippet"[^>]*>(?P<snippet>.*?)</a>',
            block,
            flags=re.IGNORECASE | re.DOTALL,
        )

        results.append(
            {
                "title": _strip_tags(link_match.group("title")),
                "url": _resolve_result_url(link_match.group("href")),
                "snippet": _strip_tags(snippet_match.group("snippet")) if snippet_match else "",
            }
        )

        if len(results) >= max_results:
            break

    return results


def _format_search_results(query: str, results: list[dict[str, str]]) -> str:
    if not results:
        return f"No search results found for: {query}"

    lines = [f"Search results for: {query}"]
    for index, result in enumerate(results, start=1):
        lines.append(f"{index}. {result['title']}")
        lines.append(f"   URL: {result['url']}")
        if result["snippet"]:
            lines.append(f"   Snippet: {result['snippet']}")
    return "\n".join(lines)


@tool
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web and return a compact list of result titles, URLs, and snippets."""
    normalized_query = query.strip()
    if not normalized_query:
        return "Search query is empty."

    normalized_max_results = max(1, min(max_results, 10))
    try:
        html = _fetch_search_html(normalized_query)
        results = _parse_search_results(html, max_results=normalized_max_results)
    except Exception as exc:
        return f"Web search failed: {exc}"
    return _format_search_results(normalized_query, results)
