"""YouTube lane — metadata + transcript via `yt-dlp` (no API key, no IP blocks).

Ported from the dig-yt agent. `yt-dlp` handles both the metadata dump and
subtitle download; we parse the json3 subtitle format into timestamped segments.
"""
from __future__ import annotations

import glob
import json
import os
import shutil
import subprocess
import tempfile

from ..errors import MissingTool
from ..models import TranscriptSegment, Video

YTDLP_HINT = "Install with: pip install yt-dlp   (or: brew install yt-dlp)"


def has_ytdlp() -> bool:
    return shutil.which("yt-dlp") is not None


def _ytdlp(*args, timeout=180):
    if not has_ytdlp():
        raise MissingTool("yt-dlp", YTDLP_HINT)
    return subprocess.run(["yt-dlp", "--no-warnings", *args],
                          capture_output=True, text=True, timeout=timeout)


def _fmt_ts(seconds):
    s = int(seconds)
    h, m, sec = s // 3600, (s % 3600) // 60, s % 60
    return "%d:%02d:%02d" % (h, m, sec) if h else "%d:%02d" % (m, sec)


def metadata(url) -> Video:
    r = _ytdlp("--skip-download", "--no-playlist", "-J", url, timeout=90)
    data = json.loads(r.stdout)
    return Video(
        video_id=data.get("id", ""), title=data.get("title", ""),
        channel=data.get("channel") or data.get("uploader", ""),
        upload_date=data.get("upload_date"), duration_s=data.get("duration"),
        description=(data.get("description") or "")[:1000],
        url=data.get("webpage_url") or url,
    )


def _parse_json3(path):
    segments = []
    try:
        with open(path) as f:
            data = json.load(f)
    except Exception:
        return segments
    for e in data.get("events", []):
        if "segs" not in e:
            continue
        text = "".join(s.get("utf8", "") for s in e["segs"]).strip()
        if not text:
            continue
        t = e.get("tStartMs", 0) / 1000.0
        segments.append(TranscriptSegment(ts=_fmt_ts(t), seconds=round(t, 2), text=text))
    return segments


def transcript(url, langs="en,en-US,en-GB,en-orig"):
    """Return (segments, language, auto_generated). Empty list if no subs exist."""
    with tempfile.TemporaryDirectory(prefix="digdeep-yt-") as d:
        _ytdlp("--skip-download", "--no-playlist", "--write-sub", "--write-auto-sub",
               "--sub-lang", langs, "--sub-format", "json3",
               "-o", os.path.join(d, "%(id)s"), url)
        files = sorted(glob.glob(os.path.join(d, "*.json3")))
        if not files:
            return [], None, None
        # Prefer a manual (non-auto) English track when present.
        chosen = files[0]
        for f in files:
            base = os.path.basename(f)
            if ".en." in base and "auto" not in base.lower():
                chosen = f
                break
        lang = os.path.basename(chosen).split(".")[-2] if "." in os.path.basename(chosen) else None
        return _parse_json3(chosen), lang, None


def fetch(url, want="both", langs="en,en-US,en-GB,en-orig"):
    """want: 'both' | 'metadata' | 'transcript'."""
    out = {}
    if want in ("both", "metadata"):
        out["video"] = metadata(url)
    if want in ("both", "transcript"):
        segs, lang, auto = transcript(url, langs=langs)
        out["segments"] = segs
        out["language"] = lang
        out["segment_count"] = len(segs)
    return out
