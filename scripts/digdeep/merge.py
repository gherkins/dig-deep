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


# Query params that identify a campaign/click, not a distinct page.
_TRACKING_PARAMS = {
    "gclid", "fbclid", "mc_cid", "mc_eid", "igshid", "ref", "ref_src",
    "_hsenc", "_hsmi", "yclid", "msclkid",
}


def _is_tracking(name: str) -> bool:
    n = name.lower()
    return n in _TRACKING_PARAMS or n.startswith("utm_")


def normalize_url(url: str) -> str:
    """Cheap URL key for dedup: drop scheme, fragment, tracking params, trailing
    slash, and a leading ``www.``. Meaningful query params are kept (sorted) so
    genuinely distinct pages (e.g. ``?v=A`` vs ``?v=B``) don't collapse together.
    """
    if not url:
        return ""
    u = url.split("://", 1)[-1].split("#", 1)[0]      # drop scheme + fragment
    path, _, query = u.partition("?")
    path = path.rstrip("/")
    if path.startswith("www."):
        path = path[4:]
    kept = sorted(p for p in query.split("&") if p and not _is_tracking(p.split("=", 1)[0]))
    if kept:
        return (path + "?" + "&".join(kept)).lower()
    return path.lower()
