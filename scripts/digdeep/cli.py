"""digdeep — a single CLI over every research lane.

    digdeep web search "q1" "q2" [-m 10] [--backends brave,mojeek]
    digdeep web fetch URL [URL ...] [--no-browser]
    digdeep papers search "query" [--sources openalex,s2] [--year-from 2022] [--open-access]
    digdeep papers read <arxiv-id | doi | url>
    digdeep papers graph <id> [--direction citations|references|related]
    digdeep reddit search "q1" "q2" [--subreddit X] [--time year]
    digdeep reddit thread <permalink> [--comments 25]
    digdeep youtube <url> [--want both|metadata|transcript]
    digdeep playlist search "query" [--top 3]
    digdeep playlist resolve refs.json
    digdeep playlist urlize ID1 ID2 ... [--label "My dig"]
    digdeep wiki "what do we know about X" [--root PATH]
    digdeep doctor

Every command prints JSON to stdout (compact by default; add -p/--pretty for
indented output). External-tool errors print to stderr and exit non-zero.
"""
from __future__ import annotations

import argparse
import json
import sys

from .models import to_jsonable


# ----------------------------------------------------------------- handlers
def _web_search(a):
    from .lanes import web
    backends = a.backends.split(",") if a.backends else None
    return web.search(a.queries, backends=backends, max_per_query=a.max)


def _web_fetch(a):
    from .lanes import web
    return web.fetch(a.urls, allow_browser=not a.no_browser)


def _papers_search(a):
    from .lanes import papers
    sources = a.sources.split(",") if a.sources else None
    return papers.search(a.query, sources=sources, per_source=a.num,
                         year_from=a.year_from, min_citations=a.min_citations,
                         open_access_only=a.open_access)


def _papers_read(a):
    from .lanes import papers
    return papers.read(a.id)


def _papers_graph(a):
    from .lanes import papers
    return papers.graph(a.id, direction=a.direction, limit=a.limit)


def _reddit_search(a):
    from .lanes import reddit
    return reddit.search(a.queries, subreddit=a.subreddit, sort=a.sort,
                         time_filter=a.time, limit=a.limit, max_candidates=a.max)


def _reddit_thread(a):
    from .lanes import reddit
    return reddit.thread(a.permalink, comment_limit=a.comments)


def _youtube(a):
    from .lanes import youtube
    return youtube.fetch(a.url, want=a.want, langs=a.lang)


def _playlist_search(a):
    from .lanes import playlist
    return playlist.search(a.query, top=a.top)


def _playlist_resolve(a):
    from .lanes import playlist
    with open(a.file) as f:
        entries = json.load(f)
    return playlist.search_batch(entries, workers=a.workers, top=a.top)


def _playlist_urlize(a):
    from .lanes import playlist
    ids = list(a.ids)
    if a.ids_file:
        with open(a.ids_file) as f:
            ids += [line.strip() for line in f if line.strip()]
    return playlist.urlize(ids, label=a.label)


def _wiki(a):
    from .lanes import wiki
    return wiki.lookup(a.question, wiki_root=a.root)


# ----------------------------------------------------------------- parser
def build_parser():
    # Shared so -p/--pretty works both before AND after the subcommand.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("-p", "--pretty", action="store_true", help="indent JSON output")

    p = argparse.ArgumentParser(prog="digdeep", description=__doc__, parents=[common],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    lanes = p.add_subparsers(dest="lane", required=True)

    # web
    web = lanes.add_parser("web", help="broad web meta-search (ddgs)")
    web_sub = web.add_subparsers(dest="action", required=True)
    ws = web_sub.add_parser("search", parents=[common], help="run search queries")
    ws.add_argument("queries", nargs="+")
    ws.add_argument("--backends", help="comma-separated ddgs backends")
    ws.add_argument("-m", "--max", type=int, default=10, help="results per query")
    ws.set_defaults(func=_web_search)
    wf = web_sub.add_parser("fetch", parents=[common], help="fetch full text of URLs")
    wf.add_argument("urls", nargs="+")
    wf.add_argument("--no-browser", action="store_true", help="disable browser fallback")
    wf.set_defaults(func=_web_fetch)

    # papers
    pa = lanes.add_parser("papers", help="academic search (OpenAlex/arXiv/S2/Crossref)")
    pa_sub = pa.add_subparsers(dest="action", required=True)
    ps = pa_sub.add_parser("search", parents=[common], help="search across sources")
    ps.add_argument("query")
    ps.add_argument("--sources", help="comma-separated: openalex,arxiv,s2,crossref")
    ps.add_argument("-n", "--num", type=int, default=25, help="results per source")
    ps.add_argument("--year-from", type=int, dest="year_from")
    ps.add_argument("--min-citations", type=int, default=0, dest="min_citations")
    ps.add_argument("--open-access", action="store_true", dest="open_access")
    ps.set_defaults(func=_papers_search)
    pr = pa_sub.add_parser("read", parents=[common], help="read full text by arXiv id / DOI / URL")
    pr.add_argument("id")
    pr.set_defaults(func=_papers_read)
    pg = pa_sub.add_parser("graph", parents=[common], help="citation graph via Semantic Scholar")
    pg.add_argument("id")
    pg.add_argument("--direction", choices=["citations", "references", "related"], default="citations")
    pg.add_argument("--limit", type=int, default=25)
    pg.set_defaults(func=_papers_graph)

    # reddit
    rd = lanes.add_parser("reddit", help="Reddit search + threads (public JSON API)")
    rd_sub = rd.add_subparsers(dest="action", required=True)
    rs = rd_sub.add_parser("search", parents=[common], help="search threads")
    rs.add_argument("queries", nargs="+")
    rs.add_argument("--subreddit")
    rs.add_argument("--sort", default="relevance")
    rs.add_argument("--time", help="time filter: hour|day|week|month|year|all")
    rs.add_argument("--limit", type=int, default=10, help="results per query")
    rs.add_argument("--max", type=int, default=10, help="max ranked candidates returned")
    rs.set_defaults(func=_reddit_search)
    rt = rd_sub.add_parser("thread", parents=[common], help="fetch a full thread")
    rt.add_argument("permalink", help="e.g. /r/sub/comments/abc123/title/")
    rt.add_argument("--comments", type=int, default=25)
    rt.set_defaults(func=_reddit_thread)

    # youtube
    yt = lanes.add_parser("youtube", parents=[common], help="video metadata + transcript (yt-dlp)")
    yt.add_argument("url")
    yt.add_argument("--want", choices=["both", "metadata", "transcript"], default="both")
    yt.add_argument("--lang", default="en,en-US,en-GB,en-orig")
    yt.set_defaults(func=_youtube)

    # playlist
    pl = lanes.add_parser("playlist", help="present videos as a watch_videos playlist")
    pl_sub = pl.add_subparsers(dest="action", required=True)
    pls = pl_sub.add_parser("search", parents=[common], help="resolve one query to videos")
    pls.add_argument("query")
    pls.add_argument("--top", type=int, default=1)
    pls.set_defaults(func=_playlist_search)
    plr = pl_sub.add_parser("resolve", parents=[common], help="batch-resolve a JSON list of {id, query}")
    plr.add_argument("file")
    plr.add_argument("--top", type=int, default=1)
    plr.add_argument("--workers", type=int, default=8)
    plr.set_defaults(func=_playlist_resolve)
    plu = pl_sub.add_parser("urlize", parents=[common], help="emit watch_videos URLs from video IDs")
    plu.add_argument("ids", nargs="*")
    plu.add_argument("--ids-file", dest="ids_file")
    plu.add_argument("--label")
    plu.set_defaults(func=_playlist_urlize)

    # wiki
    wk = lanes.add_parser("wiki", parents=[common], help="read-only lookup against .claude/wiki/")
    wk.add_argument("question")
    wk.add_argument("--root", help="explicit wiki root (else walk up from cwd)")
    wk.set_defaults(func=_wiki)

    # doctor
    dc = lanes.add_parser("doctor", help="check installed dependencies")
    dc.set_defaults(func=None)

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)

    if args.lane == "doctor":
        from . import doctor
        return doctor.main()

    try:
        result = args.func(args)
    except KeyboardInterrupt:
        return 130
    except Exception as e:
        print(json.dumps({"error": str(e), "type": type(e).__name__}), file=sys.stderr)
        return 2

    indent = 2 if args.pretty else None
    print(json.dumps(to_jsonable(result), indent=indent, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
