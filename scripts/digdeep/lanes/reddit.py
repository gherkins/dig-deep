"""Reddit lane — search + full threads via Reddit's public JSON API.

Ported from the dig-reddit agent. Reddit blocks blank UAs and rate-limits hard,
so we always send a descriptive UA and pace requests. When the JSON API is
IP-blocked (403 with an HTML "Blocked" page), we surface that clearly and — if
the optional browser extra is installed — return the rendered page text as a
best-effort fallback rather than failing outright.
"""
from __future__ import annotations

import time
import urllib.parse

from .. import http
from ..config import REDDIT_MAX_THREADS, REDDIT_RATE_SLEEP, REDDIT_USER_AGENT
from ..merge import dedupe, rank
from ..models import RedditCandidate, RedditComment, RedditThread

_HEADERS = {"User-Agent": REDDIT_USER_AGENT}


def _is_blocked(r) -> bool:
    """403 with an HTML body = IP-level block on the JSON path (not a rate limit)."""
    if r.status == 403:
        return True
    if r.status == 0 and not r.text:
        return False
    low = (r.text or "")[:2000].lower()
    return "blocked" in low and "<html" in low


def _browser_text(url, wait_text=None):
    try:
        from .. import browser
        return browser.render(url, wait_text=wait_text)
    except Exception as e:
        return "browser fallback unavailable: %s" % e


def _children(data):
    return (data or {}).get("data", {}).get("children", [])


# ---------------------------------------------------------------- search
def search(queries, subreddit=None, sort="relevance", time_filter=None,
           limit=10, max_candidates=10):
    if isinstance(queries, str):
        queries = [queries]
    candidates, blocked, note = [], False, ""

    for i, q in enumerate(queries):
        enc = urllib.parse.quote(q)
        if subreddit:
            url = ("https://www.reddit.com/r/%s/search.json?q=%s&restrict_sr=on&limit=%d&sort=%s"
                   % (subreddit, enc, limit, sort))
        else:
            url = "https://www.reddit.com/search.json?q=%s&limit=%d&sort=%s" % (enc, limit, sort)
        if time_filter:
            url += "&t=%s" % time_filter

        data, r = http.get_json(url, headers=_HEADERS)
        if _is_blocked(r):
            blocked = True
            note = "JSON API returned 403 (IP-level block on .json path)."
            break
        for c in _children(data):
            p = c.get("data", {})
            if not p.get("id"):
                continue
            candidates.append(RedditCandidate(
                id=p["id"], title=p.get("title", ""), subreddit=p.get("subreddit", ""),
                score=p.get("score", 0), num_comments=p.get("num_comments", 0),
                permalink=p.get("permalink", ""),
                url="https://www.reddit.com" + p.get("permalink", ""),
                created_utc=p.get("created_utc"),
            ))
        if i < len(queries) - 1:
            time.sleep(REDDIT_RATE_SLEEP)

    candidates = dedupe(candidates, key=lambda c: c.id)
    # score = upvotes + 2*comments (discussion is the stronger signal)
    candidates = rank(candidates, score=lambda c: c.score + 2 * c.num_comments)[:max_candidates]

    out = {"blocked": blocked, "note": note, "candidates": candidates}
    if blocked:
        first = queries[0] if queries else ""
        b_url = "https://old.reddit.com/search?q=%s&sort=relevance" % urllib.parse.quote(first)
        out["raw_text"] = _browser_text(b_url)[:8000]
    return out


# ---------------------------------------------------------------- thread
def _parse_comment(cd, max_depth, depth=0):
    if cd.get("kind") == "more" or not cd.get("body"):
        return None
    if cd.get("author") == "[deleted]" or cd.get("score", 0) < 2:
        return None
    replies = []
    if depth < max_depth:
        rep = cd.get("replies")
        if isinstance(rep, dict):
            for rc in _children(rep):
                parsed = _parse_comment(rc.get("data", {}), max_depth, depth + 1)
                if parsed:
                    replies.append(parsed)
            replies = rank(replies, score=lambda c: c.score)[:3]
    return RedditComment(author=cd.get("author", ""), score=cd.get("score", 0),
                         body=cd["body"], replies=replies)


def thread(permalink, comment_limit=25, depth=2):
    url = "https://www.reddit.com%s/.json?limit=%d&depth=%d&sort=top" % (
        permalink.rstrip("/"), comment_limit, depth)
    data, r = http.get_json(url, headers=_HEADERS)
    if _is_blocked(r) or not isinstance(data, list):
        b_url = "https://old.reddit.com%s/" % permalink.rstrip("/")
        return {"blocked": True, "note": "JSON blocked; rendered HTML fallback.",
                "permalink": permalink, "raw_text": _browser_text(b_url, wait_text="comments")[:12000]}

    post = data[0]["data"]["children"][0]["data"]
    comments = []
    for c in _children(data[1]):
        parsed = _parse_comment(c.get("data", {}), max_depth=depth)
        if parsed:
            comments.append(parsed)
    comments = rank(comments, score=lambda c: c.score)[:comment_limit]

    t = RedditThread(
        title=post.get("title", ""), subreddit=post.get("subreddit", ""),
        author=post.get("author", ""), score=post.get("score", 0),
        num_comments=post.get("num_comments", 0),
        url="https://www.reddit.com" + post.get("permalink", ""),
        selftext=(post.get("selftext", "") or "")[:2000], comments=comments,
    )
    return {"blocked": False, "note": "", "thread": t}


def threads(permalinks, comment_limit=25):
    """Fetch several threads, pacing requests. Caps at REDDIT_MAX_THREADS."""
    out = []
    for i, pl in enumerate(permalinks[:REDDIT_MAX_THREADS]):
        out.append(thread(pl, comment_limit=comment_limit))
        if i < len(permalinks) - 1:
            time.sleep(REDDIT_RATE_SLEEP)
    return out
