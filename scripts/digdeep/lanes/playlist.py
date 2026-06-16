"""Playlist lane — present a set of YouTube videos as a clickable playlist.

A results-presentation helper (not a standalone research lane). Given video IDs
the research already surfaced, `urlize` emits YouTube `watch_videos` URLs — a
temporary playlist the user opens and saves with one click (no Data API, no
OAuth, no quota). `search` / `search_batch` resolve free-text references to
video IDs via yt-dlp when the report mentions titles rather than IDs.

Ported from the standalone yt_playlist.py helper.
"""
from __future__ import annotations

import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..errors import MissingTool
from .youtube import YTDLP_HINT, has_ytdlp

WATCH_VIDEOS_LIMIT = 50  # YouTube's hard cap per watch_videos URL
_PRINT_FMT = "%(id)s\t%(title)s\t%(channel)s\t%(duration)s\t%(view_count)s\t%(upload_date)s"


def _run_search(query, top=1, timeout=60):
    if not has_ytdlp():
        raise MissingTool("yt-dlp", YTDLP_HINT)
    r = subprocess.run(
        ["yt-dlp", "--no-warnings", "--skip-download", "--print", _PRINT_FMT,
         "ytsearch%d:%s" % (top, query)],
        capture_output=True, text=True, timeout=timeout,
    )
    out = []
    for line in r.stdout.strip().splitlines():
        parts = line.split("\t")
        if len(parts) < 6:
            continue
        vid, title, channel, dur, views, uploaded = parts[:6]
        out.append({
            "video_id": vid, "video_title": title, "channel": channel,
            "duration_s": int(dur) if dur and dur != "NA" else None,
            "view_count": int(views) if views and views != "NA" else None,
            "upload_date": uploaded if uploaded != "NA" else None,
            "url": "https://www.youtube.com/watch?v=%s" % vid,
        })
    return out


def search(query, top=1):
    return _run_search(query, top=top)


def _resolve_one(entry, top):
    if entry.get("video_id"):
        entry.setdefault("status", "ok")
        return entry
    q = entry.get("query")
    if not q:
        entry["status"] = "no_query"
        return entry
    try:
        cands = _run_search(q, top=top)
        if not cands:
            entry["status"] = "search_empty"
            return entry
        entry.update(cands[0])
        if top > 1:
            entry["candidates"] = cands
        entry["status"] = "ok"
    except subprocess.TimeoutExpired:
        entry["status"] = "timeout"
    except Exception as e:
        entry["status"] = "exception"
        entry["error"] = str(e)
    return entry


def search_batch(entries, workers=8, top=1):
    """entries: list of {id?, query, ...}. Resolves to video_ids in parallel."""
    indexed = list(enumerate(entries))
    out = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(_resolve_one, dict(e), top): i for i, e in indexed}
        for fut in as_completed(futs):
            out.append((futs[fut], fut.result()))
    out.sort(key=lambda x: x[0])
    return [r for _, r in out]


def _chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def urlize(video_ids, label=None):
    """Emit watch_videos URLs (chunked at 50). Returns a list of {url, video_count, label?}."""
    ids = [v.strip() for v in video_ids if v and v.strip()]
    chunks = list(_chunks(ids, WATCH_VIDEOS_LIMIT))
    out = []
    for i, chunk in enumerate(chunks, 1):
        item = {"url": "https://www.youtube.com/watch_videos?video_ids=" + ",".join(chunk),
                "video_count": len(chunk)}
        if label:
            item["label"] = label + (" (part %d/%d)" % (i, len(chunks)) if len(chunks) > 1 else "")
        out.append(item)
    return out
