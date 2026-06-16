"""Generic dedupe + rank helpers used by the search lanes."""
from __future__ import annotations


def dedupe(items, key):
    """Keep the first occurrence per `key(item)`. Falsy keys are kept as-is."""
    seen = set()
    out = []
    for it in items:
        k = key(it)
        if k and k in seen:
            continue
        if k:
            seen.add(k)
        out.append(it)
    return out


def rank(items, score, reverse=True):
    """Stable sort by `score(item)`."""
    return sorted(items, key=score, reverse=reverse)


def normalize_url(url: str) -> str:
    """Cheap URL key for dedup: drop scheme, trailing slash, and a leading www."""
    if not url:
        return ""
    u = url.split("://", 1)[-1].rstrip("/")
    if u.startswith("www."):
        u = u[4:]
    return u.lower()
