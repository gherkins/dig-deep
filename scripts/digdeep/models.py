"""Lightweight record types shared across lanes, plus JSON serialization.

Lanes build these dataclasses; the CLI serializes them with `to_jsonable`.
Keeping the shapes in one place means the web/reddit/papers/youtube outputs are
predictable for any consumer (an LLM, a shell pipeline, or a test).
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SearchHit:
    title: str
    url: str
    snippet: str = ""
    backend: str = ""
    query: str = ""


@dataclass
class Paper:
    title: str
    year: Optional[int] = None
    authors: str = ""
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    oa_url: Optional[str] = None
    abstract: Optional[str] = None
    cited_by: int = 0
    s2_id: Optional[str] = None
    # Which source APIs surfaced this paper (sorted list, deduped).
    sources: List[str] = field(default_factory=list)


@dataclass
class RedditComment:
    author: str
    score: int
    body: str
    replies: List["RedditComment"] = field(default_factory=list)


@dataclass
class RedditCandidate:
    id: str
    title: str
    subreddit: str
    score: int
    num_comments: int
    permalink: str
    url: str = ""
    created_utc: Optional[float] = None


@dataclass
class RedditThread:
    title: str
    subreddit: str
    author: str
    score: int
    num_comments: int
    url: str
    selftext: str = ""
    comments: List[RedditComment] = field(default_factory=list)


@dataclass
class Video:
    video_id: str
    title: str = ""
    channel: str = ""
    upload_date: Optional[str] = None
    duration_s: Optional[int] = None
    description: str = ""
    url: str = ""


@dataclass
class TranscriptSegment:
    ts: str          # human-readable timestamp, e.g. "12:03"
    seconds: float   # start time in seconds
    text: str


def to_jsonable(obj):
    """Recursively convert dataclasses / sets / nested containers to JSON-safe types."""
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {k: to_jsonable(v) for k, v in dataclasses.asdict(obj).items()}
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    if isinstance(obj, set):
        return sorted(to_jsonable(v) for v in obj)
    return obj
