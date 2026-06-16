"""HTML → readable text, and a page fetcher with an optional browser fallback.

`html_to_text` uses `trafilatura` when installed (much better extraction) and
falls back to a dependency-free stdlib stripper otherwise. `fetch_page` is what
the lanes call: it fetches over HTTP, extracts text, and — if the result looks
blocked or sparse — transparently retries through a headless browser when the
optional `[browser]` extra is installed.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser

from . import http
from .config import SPARSE_TEXT_THRESHOLD

_SKIP_TAGS = {"script", "style", "noscript", "template", "svg", "head", "nav", "footer"}
_BLOCK_TAGS = {"p", "br", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6",
               "section", "article", "header", "blockquote", "pre"}

_BLOCK_MARKERS = (
    "enable javascript", "captcha", "are you a robot", "verify you are human",
    "cloudflare", "access denied", "request blocked", "ddos protection",
)


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in _SKIP_TAGS:
            self._skip_depth += 1
        elif tag in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in _SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data):
        if self._skip_depth == 0:
            self.parts.append(data)


def html_to_text(html: str) -> str:
    if not html:
        return ""
    try:
        import trafilatura  # optional [extract] extra
        extracted = trafilatura.extract(html, include_comments=False, include_tables=True)
        if extracted and len(extracted.strip()) >= 200:
            return extracted.strip()
    except Exception:
        pass
    parser = _TextExtractor()
    try:
        parser.feed(html)
    except Exception:
        pass
    text = "".join(parser.parts)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n[ \t]*", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def looks_blocked(text: str, status: int) -> bool:
    if status and status >= 400:
        return True
    if status == 0:
        return True
    stripped = (text or "").strip()
    if len(stripped) < SPARSE_TEXT_THRESHOLD:
        return True
    low = stripped[:4000].lower()
    return any(m in low for m in _BLOCK_MARKERS)


def fetch_page(url, allow_browser=True, browser_wait=None) -> dict:
    """Fetch a URL and return {url, status, text, via, blocked, note}.

    `via` is "http" or "browser". When the HTTP result looks blocked/sparse and
    the browser extra is available, the rendered DOM text is used instead.
    """
    r = http.get(url)
    text = html_to_text(r.text)
    out = {"url": r.url or url, "status": r.status, "text": text, "via": "http",
           "blocked": looks_blocked(text, r.status), "note": r.error or ""}

    if out["blocked"] and allow_browser:
        try:
            from . import browser
            rendered = browser.render(url, wait_text=browser_wait)
            btext = html_to_text(rendered) if "<" in rendered[:200] else rendered.strip()
            if len(btext) > len(text):
                out.update(text=btext, via="browser", blocked=looks_blocked(btext, 200), note="")
        except Exception as e:
            # Browser missing or failed — keep the HTTP result, annotate why.
            out["note"] = (out["note"] + " | " if out["note"] else "") + "browser fallback unavailable: %s" % e
    return out
