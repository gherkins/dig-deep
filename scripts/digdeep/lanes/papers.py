"""Papers lane — academic search across OpenAlex, arXiv, Semantic Scholar, Crossref.

Ported from the dig-papers agent. All four APIs are free and keyless. `search`
queries them (in parallel), dedupes by DOI/title, and ranks by citations.
`read` pulls full text (ar5iv for arXiv, else the page). `graph` walks the
Semantic Scholar citation graph.
"""
from __future__ import annotations

import re
import urllib.parse
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

from .. import http, render
from ..config import PAPERS_SOURCES
from ..merge import rank
from ..models import Paper

S2_BASE = "https://api.semanticscholar.org/graph/v1"
_ARXIV_RE = re.compile(r"^\d{4}\.\d{4,5}(v\d+)?$|^[a-z\-]+(\.[A-Z]{2})?/\d{7}(v\d+)?$")


# ---------------------------------------------------------------- inverted index
def _abstract_from_inverted_index(inv):
    if not inv:
        return None
    try:
        size = max(max(pos) for pos in inv.values()) + 1
        words = [""] * size
        for word, positions in inv.items():
            for p in positions:
                words[p] = word
        return " ".join(words)[:600].strip()
    except Exception:
        return None


# ---------------------------------------------------------------- per-source fetchers
def _openalex(query, per_source):
    q = urllib.parse.quote(query)
    data, _ = http.get_json("https://api.openalex.org/works?search=%s&per_page=%d" % (q, per_source))
    out = []
    for w in (data or {}).get("results", []):
        out.append(dict(
            doi=(w.get("doi") or "").replace("https://doi.org/", "") or None,
            title=w.get("title", "") or "",
            year=w.get("publication_year"),
            cited_by=w.get("cited_by_count", 0),
            source="OpenAlex",
            oa_url=(w.get("open_access") or {}).get("oa_url"),
            abstract=_abstract_from_inverted_index(w.get("abstract_inverted_index")),
            authors=", ".join(a.get("raw_author_name", "") for a in (w.get("authorships") or [])[:5]),
        ))
    return out


def _arxiv(query, per_source):
    q = urllib.parse.quote(query)
    r = http.get("https://export.arxiv.org/api/query?search_query=all:%s&sortBy=relevance&max_results=%d" % (q, per_source))
    out = []
    if not r.text:
        return out
    ns = {"a": "http://www.w3.org/2005/Atom"}
    try:
        root = ET.fromstring(r.text)
    except ET.ParseError:
        return out
    for e in root.findall("a:entry", ns):
        try:
            title = " ".join(e.find("a:title", ns).text.split())
            arxiv_id = e.find("a:id", ns).text.split("/abs/")[-1]
            year = int(e.find("a:published", ns).text[:4])
            abstract = " ".join(e.find("a:summary", ns).text.split())[:600]
            authors = ", ".join(a.find("a:name", ns).text for a in e.findall("a:author", ns)[:5])
            doi_el = e.find("{http://arxiv.org/schemas/atom}doi")
            out.append(dict(
                doi=doi_el.text if doi_el is not None else None,
                title=title, year=year, cited_by=0, source="arXiv",
                oa_url="https://ar5iv.labs.arxiv.org/html/%s" % arxiv_id,
                abstract=abstract, arxiv_id=arxiv_id, authors=authors,
            ))
        except Exception:
            continue
    return out


def _s2(query, per_source):
    q = urllib.parse.quote(query)
    fields = "title,year,citationCount,authors,abstract,openAccessPdf,externalIds"
    data, _ = http.get_json(
        "%s/paper/search/bulk?query=%s&limit=%d&fields=%s" % (S2_BASE, q, per_source, fields))
    out = []
    for p in (data or {}).get("data", []):
        ext = p.get("externalIds") or {}
        out.append(dict(
            doi=ext.get("DOI"), title=p.get("title", "") or "", year=p.get("year"),
            cited_by=p.get("citationCount", 0), source="S2",
            oa_url=(p.get("openAccessPdf") or {}).get("url"),
            abstract=(p.get("abstract") or "")[:600] or None,
            arxiv_id=ext.get("ArXiv"), s2_id=p.get("paperId"),
            authors=", ".join(a["name"] for a in (p.get("authors") or [])[:5]),
        ))
    return out


def _crossref(query, per_source):
    q = urllib.parse.quote(query)
    data, _ = http.get_json("https://api.crossref.org/works?query=%s&rows=%d&sort=relevance" % (q, per_source))
    out = []
    for it in (data or {}).get("message", {}).get("items", []):
        year = (it.get("published-print") or it.get("published-online") or it.get("created", {})) \
            .get("date-parts", [[None]])[0][0]
        out.append(dict(
            doi=it.get("DOI"), title=(it.get("title") or ["Untitled"])[0],
            year=year, cited_by=it.get("is-referenced-by-count", 0), source="Crossref",
            authors=", ".join(("%s %s" % (a.get("given", ""), a.get("family", ""))).strip()
                              for a in (it.get("author") or [])[:5]),
        ))
    return out


_FETCHERS = {"openalex": _openalex, "arxiv": _arxiv, "s2": _s2, "crossref": _crossref}


# ---------------------------------------------------------------- search
def search(query, sources=None, per_source=25, year_from=None, min_citations=0, open_access_only=False):
    sources = [s.lower() for s in (sources or PAPERS_SOURCES) if s.lower() in _FETCHERS]
    merged = {}

    def add(rec):
        title = rec.get("title")
        if not title:
            return
        key = (rec.get("doi") or title[:80]).lower().strip()
        if key in merged:
            p = merged[key]
            p.cited_by = max(p.cited_by, rec.get("cited_by") or 0)
            if rec["source"] not in p.sources:
                p.sources.append(rec["source"])
            p.oa_url = p.oa_url or rec.get("oa_url")
            p.abstract = p.abstract or rec.get("abstract")
            p.arxiv_id = p.arxiv_id or rec.get("arxiv_id")
            p.s2_id = p.s2_id or rec.get("s2_id")
            p.doi = p.doi or rec.get("doi")
        else:
            merged[key] = Paper(
                title=title, year=rec.get("year"), authors=rec.get("authors", ""),
                doi=rec.get("doi"), arxiv_id=rec.get("arxiv_id"), oa_url=rec.get("oa_url"),
                abstract=rec.get("abstract"), cited_by=rec.get("cited_by") or 0,
                s2_id=rec.get("s2_id"), sources=[rec["source"]],
            )

    with ThreadPoolExecutor(max_workers=len(sources) or 1) as ex:
        results = ex.map(lambda s: _FETCHERS[s](query, per_source), sources)
        for recs in results:
            for rec in recs:
                add(rec)

    papers = rank(list(merged.values()), score=lambda p: p.cited_by)
    if year_from:
        papers = [p for p in papers if (p.year or 0) >= year_from]
    if min_citations:
        papers = [p for p in papers if p.cited_by >= min_citations]
    if open_access_only:
        papers = [p for p in papers if p.oa_url]
    for p in papers:
        p.sources = sorted(p.sources)
    return papers


# ---------------------------------------------------------------- read
def _is_arxiv(pid):
    return bool(_ARXIV_RE.match(pid))


def _s2_paper_id(pid):
    """Normalize an id to a form Semantic Scholar's /paper/ endpoints accept.

    S2 needs a typed id (``ArXiv:<id>``, ``DOI:<doi>``, ``CorpusId:<n>``, …) or a
    40-char paperId. `search`/`graph` emit bare arXiv ids and DOIs, so prefix
    those; pass through anything already typed or an S2 paperId.
    """
    pid = (pid or "").strip()
    if not pid:
        return pid
    if ":" in pid and not pid.startswith("10."):   # already typed (ArXiv:, DOI:, CorpusId:, …)
        return pid
    if _is_arxiv(pid):
        return "ArXiv:" + pid
    if pid.startswith("10.") or "/" in pid:        # looks like a DOI
        return "DOI:" + pid
    return pid                                     # assume an S2 paperId


def _s2_detail(pid):
    fields = "title,abstract,year,citationCount,referenceCount,authors,openAccessPdf,tldr"
    data, _ = http.get_json("%s/paper/%s?fields=%s" % (S2_BASE, urllib.parse.quote(pid, safe=":/"), fields))
    return data


def read(paper_id):
    """Fetch readable content for a paper. Accepts an arXiv id, a DOI, or a URL."""
    pid = (paper_id or "").strip()
    if pid.startswith("http"):
        page = render.fetch_page(pid)
        return {"id": pid, "kind": "url", **page}
    if _is_arxiv(pid):
        url = "https://ar5iv.labs.arxiv.org/html/%s" % pid
        page = render.fetch_page(url)
        return {"id": pid, "kind": "arxiv", "source_url": url, **page}

    # Treat as DOI: pull S2 metadata + abstract + TL;DR, then OA full text if available.
    detail = _s2_detail("DOI:" + pid) or {}
    oa = (detail.get("openAccessPdf") or {}).get("url")
    out = {
        "id": pid, "kind": "doi",
        "title": detail.get("title"), "year": detail.get("year"),
        "citation_count": detail.get("citationCount"),
        "tldr": (detail.get("tldr") or {}).get("text"),
        "abstract": detail.get("abstract"),
        "oa_url": oa,
    }
    if oa and oa.lower().endswith(("html", "htm")) or (oa and "arxiv" in (oa or "")):
        page = render.fetch_page(oa)
        out["text"] = page.get("text")
        out["via"] = page.get("via")
    return out


# ---------------------------------------------------------------- citation graph
def graph(paper_id, direction="citations", limit=25):
    """direction: 'citations' | 'references' | 'related'. Returns ranked Paper list."""
    pid = urllib.parse.quote(_s2_paper_id(paper_id), safe=":/")
    fields = "title,year,citationCount,authors,abstract"
    if direction == "related":
        data, _ = http.get_json(
            "https://api.semanticscholar.org/recommendations/v1/papers/forpaper/%s?limit=%d&fields=%s"
            % (pid, limit, fields))
        rows = (data or {}).get("recommendedPapers", [])
    else:
        key = "citingPaper" if direction == "citations" else "citedPaper"
        data, _ = http.get_json("%s/paper/%s/%s?limit=%d&fields=%s" % (S2_BASE, pid, direction, limit, fields))
        rows = [r.get(key, {}) for r in (data or {}).get("data", [])]

    papers = []
    for p in rows:
        if not p or not p.get("title"):
            continue
        ext = p.get("externalIds") or {}
        papers.append(Paper(
            title=p.get("title", ""), year=p.get("year"), cited_by=p.get("citationCount", 0),
            authors=", ".join(a["name"] for a in (p.get("authors") or [])[:3]),
            doi=ext.get("DOI"), arxiv_id=ext.get("ArXiv"), s2_id=p.get("paperId"),
            abstract=(p.get("abstract") or "")[:400] or None, sources=["S2"],
        ))
    return rank(papers, score=lambda p: p.cited_by)
