"""Shared configuration — user agents, backends, timeouts, and limits.

Every value here can be overridden via an environment variable so the tools
can be tuned without code changes (handy when embedding them in a workflow).
"""
import os


def _int(name, default):
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _float(name, default):
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


# Generic HTTP
USER_AGENT = os.environ.get(
    "DIGDEEP_USER_AGENT",
    "digdeep-research/0.1 (+https://github.com/gherkins/dig-deep)",
)
HTTP_TIMEOUT = _int("DIGDEEP_HTTP_TIMEOUT", 20)

# A fetched page shorter than this (chars of extracted text) is treated as
# "sparse" — likely a bot wall or JS-only page — and is worth a browser retry.
SPARSE_TEXT_THRESHOLD = _int("DIGDEEP_SPARSE_THRESHOLD", 500)

# Web lane (ddgs meta-search). `google` is intentionally omitted — it is
# frequently IP-rate-limited and returns "No results found".
DDGS_BACKENDS = os.environ.get(
    "DIGDEEP_DDGS_BACKENDS", "duckduckgo,brave,mojeek,yandex"
).split(",")

# Reddit lane. Reddit blocks blank/default UAs outright.
REDDIT_USER_AGENT = os.environ.get(
    "DIGDEEP_REDDIT_UA",
    "digdeep-research/0.1 (reddit lane; +https://github.com/gherkins/dig-deep)",
)
REDDIT_RATE_SLEEP = _float("DIGDEEP_REDDIT_SLEEP", 2.0)   # seconds between calls
REDDIT_MAX_THREADS = _int("DIGDEEP_REDDIT_MAX_THREADS", 10)

# Academic-papers lane sources (any subset of these names).
PAPERS_SOURCES = ["openalex", "arxiv", "s2", "crossref"]
