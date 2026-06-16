"""Web lane — broad meta-search via the `ddgs` CLI, plus full-page fetch.

Ported from the dig-meta agent. `ddgs` aggregates DuckDuckGo, Brave, Mojeek,
Yandex and others through one CLI (no API keys). We run several queries across
rotated backends in parallel, then dedupe by URL. `fetch` reads the full text
of chosen URLs (with the optional browser fallback for blocked pages).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed

from .. import render
from ..config import DDGS_BACKENDS
from ..errors import MissingTool
from ..merge import dedupe, normalize_url
from ..models import SearchHit

DDGS_HINT = "Install with: pipx install ddgs   (or: pip install ddgs)"


def has_ddgs() -> bool:
    return shutil.which("ddgs") is not None


def _ddgs_one(query, backend, max_results, timeout) -> list:
    """Run one `ddgs text` query. ddgs only writes JSON to a file, never stdout."""
    fd, path = tempfile.mkstemp(suffix=".json", prefix="digdeep-ddgs-")
    os.close(fd)
    try:
        subprocess.run(
            ["ddgs", "text", "-q", query, "-b", backend, "-m", str(max_results), "-o", path],
            capture_output=True, text=True, timeout=timeout,
        )
        with open(path) as f:
            data = json.load(f)
    except Exception:
        return []
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
    hits = []
    for r in data if isinstance(data, list) else []:
        url = r.get("href") or r.get("url") or ""
        if not url:
            continue
        hits.append(SearchHit(
            title=r.get("title", ""), url=url,
            snippet=(r.get("body") or "")[:300], backend=backend, query=query,
        ))
    return hits


def search(queries, backends=None, max_per_query=10, workers=6, timeout=30) -> list:
    """Run `queries` across rotated backends in parallel; return deduped SearchHits."""
    if not has_ddgs():
        raise MissingTool("ddgs", DDGS_HINT)
    if isinstance(queries, str):
        queries = [queries]
    backends = backends or DDGS_BACKENDS
    pairs = [(q, backends[i % len(backends)]) for i, q in enumerate(queries)]

    hits = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(_ddgs_one, q, b, max_per_query, timeout) for q, b in pairs]
        for fut in as_completed(futs):
            hits.extend(fut.result())
    return dedupe(hits, key=lambda h: normalize_url(h.url))


def fetch(urls, allow_browser=True) -> list:
    """Fetch full readable text for each URL (sequential — the browser path is not thread-safe)."""
    if isinstance(urls, str):
        urls = [urls]
    return [render.fetch_page(u, allow_browser=allow_browser) for u in urls]
