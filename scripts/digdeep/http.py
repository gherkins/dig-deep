"""Minimal HTTP GET built on the stdlib (no `requests` dependency).

Returns a uniform `HttpResult` for both success and failure so lanes never have
to wrap calls in try/except just to read a status code.
"""
from __future__ import annotations

import gzip
import json as _json
import urllib.error
import urllib.request
import zlib
from dataclasses import dataclass
from typing import Optional

from .config import HTTP_TIMEOUT, USER_AGENT


@dataclass
class HttpResult:
    url: str
    status: int          # 0 means the request never completed (network error)
    text: str
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300


def _decompress(raw: bytes, encoding: str) -> bytes:
    encoding = (encoding or "").lower()
    try:
        if "gzip" in encoding:
            return gzip.decompress(raw)
        if "deflate" in encoding:
            return zlib.decompress(raw)
    except Exception:
        pass
    return raw


def get(url, headers=None, timeout=HTTP_TIMEOUT, ua=USER_AGENT) -> HttpResult:
    """Fetch a URL. Never raises — failures come back as an HttpResult with a status/error."""
    hdrs = {"User-Agent": ua, "Accept": "*/*", "Accept-Encoding": "gzip, deflate"}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = _decompress(resp.read(), resp.headers.get("Content-Encoding", ""))
            charset = resp.headers.get_content_charset() or "utf-8"
            return HttpResult(resp.geturl(), resp.getcode(), raw.decode(charset, "replace"))
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = _decompress(e.read(), e.headers.get("Content-Encoding", "") if e.headers else "").decode("utf-8", "replace")
        except Exception:
            pass
        return HttpResult(url, e.code, body, error="HTTP %s" % e.code)
    except Exception as e:  # URLError, timeout, ssl, etc.
        return HttpResult(url, 0, "", error=str(e))


def get_json(url, headers=None, timeout=HTTP_TIMEOUT, ua=USER_AGENT):
    """Return (parsed_json_or_None, HttpResult). JSON parse errors leave data=None."""
    r = get(url, headers=headers, timeout=timeout, ua=ua)
    data = None
    if r.text:
        try:
            data = _json.loads(r.text)
        except ValueError:
            data = None
    return data, r
