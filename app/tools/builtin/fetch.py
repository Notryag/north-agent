from __future__ import annotations

import re
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from langchain_core.tools import tool

DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible; DeerFlowLite/0.1)"


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._ignored_depth = 0
        self._in_title = False
        self._title_parts: list[str] = []
        self._text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in {"script", "style", "noscript"}:
            self._ignored_depth += 1
            return
        if tag == "title":
            self._in_title = True
        if tag in {"p", "div", "br", "li", "section", "article", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self._text_parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._ignored_depth > 0:
            self._ignored_depth -= 1
            return
        if tag == "title":
            self._in_title = False
        if tag in {"p", "div", "br", "li", "section", "article"}:
            self._text_parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._ignored_depth > 0:
            return
        if self._in_title:
            self._title_parts.append(data)
        self._text_parts.append(data)

    @property
    def title(self) -> str:
        return _normalize_text("".join(self._title_parts))

    @property
    def text(self) -> str:
        return _normalize_text("".join(self._text_parts))


def _normalize_text(value: str) -> str:
    text = unescape(value)
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _fetch_url_html(url: str) -> str:
    request = Request(url, headers={"User-Agent": DEFAULT_USER_AGENT})
    with urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", errors="replace")


def _extract_page_content(html: str) -> tuple[str, str]:
    parser = _HTMLTextExtractor()
    parser.feed(html)
    return parser.title, parser.text


def _truncate_text(text: str, *, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    cutoff = max_chars - len("\n\n...[truncated]")
    return f"{text[:cutoff].rstrip()}\n\n...[truncated]"


@tool
def web_fetch(url: str, max_chars: int = 4000) -> str:
    """Fetch a web page and return a compact plain-text version of its title and main content."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return f"Unsupported URL scheme for fetch: {url}"

    normalized_max_chars = max(500, min(max_chars, 20000))
    try:
        html = _fetch_url_html(url)
        title, text = _extract_page_content(html)
    except Exception as exc:
        return f"Web fetch failed: {exc}"
    body = _truncate_text(text, max_chars=normalized_max_chars)

    lines = [f"Fetched URL: {url}"]
    if title:
        lines.append(f"Title: {title}")
    lines.append("Content:")
    lines.append(body or "(no text content extracted)")
    return "\n".join(lines)
