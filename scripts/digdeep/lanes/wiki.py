"""Wiki lane — read-only lookup against a per-repo research wiki.

Ported from the dig-wiki agent. Walks up from a starting directory to find a
`.claude/wiki/`, then answers "what do we already know about X?" from the index,
glossary, and page summaries. Never writes anything.
"""
from __future__ import annotations

import glob
import os
import re

_STOPWORDS = {
    "the", "and", "for", "with", "what", "which", "that", "this", "from", "into",
    "about", "your", "our", "are", "was", "were", "how", "why", "when", "who",
    "does", "did", "can", "should", "would", "could", "best", "vs", "versus",
}
_PAGE_RE = re.compile(r"\(([^)]+\.md)\)")
_TAG_RE = re.compile(r"#([\w][\w\-]*)")


def find_wiki(start=None):
    """Walk up from `start` (default cwd) looking for `.claude/wiki/`. Returns path or None."""
    d = os.path.abspath(start or os.getcwd())
    while True:
        candidate = os.path.join(d, ".claude", "wiki")
        if os.path.isdir(candidate):
            return candidate
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def _terms(question):
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9\-\.]+", question or "")
    out = []
    seen = set()
    for w in words:
        lw = w.lower()
        if lw in _STOPWORDS or len(lw) < 4 or lw in seen:
            continue
        seen.add(lw)
        out.append(lw)
    return out[:8]


def _frontmatter(text):
    fm = {}
    if not text.startswith("---"):
        return fm
    end = text.find("\n---", 3)
    if end == -1:
        return fm
    for line in text[3:end].splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip()
    return fm


def _section(text, header, max_lines=12):
    lines = text.splitlines()
    out = []
    capturing = False
    for line in lines:
        if line.strip().lower() == header.lower():
            capturing = True
            continue
        if capturing:
            if line.startswith("## "):
                break
            out.append(line)
            if len(out) >= max_lines:
                break
    return "\n".join(out).strip()


def lookup(question, wiki_root=None, max_pages=15):
    root = wiki_root or find_wiki()
    if not root or not os.path.isdir(root):
        return {"no_wiki": True, "wiki_root": None,
                "message": "No .claude/wiki/ found by walking up from the current directory."}

    terms = _terms(question)
    result = {"no_wiki": False, "wiki_root": root, "terms": terms,
              "glossary": [], "relevant_pages": [], "contradictions": [], "gaps": []}

    # --- index.md: collect candidate pages + matched tags ---
    index_path = os.path.join(root, "index.md")
    hit_tags, candidate_pages = set(), []
    if os.path.isfile(index_path):
        with open(index_path, errors="replace") as f:
            for line in f:
                low = line.lower()
                if not any(t in low for t in terms):
                    continue
                hit_tags.update(_TAG_RE.findall(line))
                for m in _PAGE_RE.findall(line):
                    if m not in candidate_pages:
                        candidate_pages.append(m)

    # --- glossary: only domain files matching a hit tag / term ---
    gloss_dir = os.path.join(root, "glossary")
    if os.path.isdir(gloss_dir):
        for path in sorted(glob.glob(os.path.join(gloss_dir, "*.yaml"))):
            stem = os.path.splitext(os.path.basename(path))[0]
            if stem.startswith("_"):
                continue
            if stem not in hit_tags and not any(t in stem for t in terms):
                continue
            with open(path, errors="replace") as f:
                for line in f:
                    if any(t in line.lower() for t in terms) and ":" in line:
                        entry = line.strip()
                        if entry and not entry.startswith("#"):
                            result["glossary"].append("%s  [#%s]" % (entry[:160], stem))
        result["glossary"] = result["glossary"][:20]

    # --- page summaries (Summary + Contradictions only) ---
    for rel in candidate_pages[:max_pages]:
        page_path = os.path.join(root, rel)
        if not os.path.isfile(page_path):
            continue
        with open(page_path, errors="replace") as f:
            text = f.read()
        fm = _frontmatter(text)
        summary = _section(text, "## Summary")
        contradictions = _section(text, "## Contradictions")
        if not summary and not contradictions:
            continue
        result["relevant_pages"].append({
            "path": rel,
            "title": fm.get("title", ""),
            "confidence": fm.get("confidence", ""),
            "last_verified": fm.get("last_verified", ""),
            "summary": summary,
        })
        if contradictions and contradictions.lower() not in ("none", "- none"):
            result["contradictions"].append({"path": rel, "text": contradictions})
        if fm.get("confidence", "").lower() in ("low", "contested"):
            result["gaps"].append("%s (confidence: %s)" % (rel, fm.get("confidence")))

    has_any = result["relevant_pages"] or result["glossary"]
    result["coverage"] = ("Wiki has %d relevant page(s) and %d glossary match(es)."
                          % (len(result["relevant_pages"]), len(result["glossary"]))) \
        if has_any else "none — the wiki has nothing on this topic yet."
    return result
