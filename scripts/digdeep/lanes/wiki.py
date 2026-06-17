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


def _has_yaml():
    try:
        import yaml  # noqa: F401
        return True
    except ImportError:
        return False


def _load_yaml(path):
    """Parse a YAML file with PyYAML. Returns a dict (possibly empty), or None when
    PyYAML isn't installed (the signal to fall back to substring matching)."""
    try:
        import yaml
    except ImportError:
        return None
    try:
        with open(path, errors="replace") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _glossary_substring(gloss_dir, terms, hit_tags):
    """Fallback used when PyYAML is absent: the original line-substring scan, but
    emitting the same dict shape as the structured path (flagged ``degraded``)."""
    out = []
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
                        out.append({
                            "term": entry.split(":", 1)[0].strip()[:80],
                            "definition": entry[:160], "domain": stem,
                            "aliases": [], "related": [], "pages": [],
                            "via": "direct", "degraded": True,
                        })
    return out[:20]


def _glossary_subgraph(gloss_dir, terms, max_entries=20):
    """Structured glossary lookup (PyYAML): direct term/alias/definition matches
    across all domains, plus one hop along each match's ``related:`` edges
    (cross-domain terms resolved via ``_aliases.yaml``)."""
    domains = {}
    for path in sorted(glob.glob(os.path.join(gloss_dir, "*.yaml"))):
        stem = os.path.splitext(os.path.basename(path))[0]
        if stem.startswith("_"):
            continue
        data = _load_yaml(path)
        if isinstance(data, dict):
            domains[stem] = data

    amap = _load_yaml(os.path.join(gloss_dir, "_aliases.yaml")) or {}
    alias_map = {str(k).lower(): str(v) for k, v in amap.items()} if isinstance(amap, dict) else {}

    def matches(name, entry):
        nl = name.lower()
        al = [str(a).lower() for a in (entry.get("aliases") or []) if a]
        defn = str(entry.get("definition") or "").lower()
        return any(t in nl or t in defn or any(t in a for a in al) for t in terms)

    def find_entry(term):
        """Resolve a related-edge term to (domain, name, entry); alias map first."""
        tl = term.lower()
        order = [alias_map[tl]] if alias_map.get(tl) in domains else []
        order += [d for d in domains if d not in order]
        for d in order:
            for k, v in domains[d].items():
                if not isinstance(v, dict):
                    continue
                if k.lower() == tl or tl in [str(a).lower() for a in (v.get("aliases") or [])]:
                    return d, k, v
        return None

    seen, out = set(), []

    def emit(domain, name, entry, via):
        keyid = (domain, name.lower())
        if keyid in seen or not isinstance(entry, dict):
            return
        seen.add(keyid)
        out.append({
            "term": name, "definition": entry.get("definition"),
            "domain": entry.get("domain") or domain,
            "aliases": entry.get("aliases") or [], "related": entry.get("related") or [],
            "pages": entry.get("pages") or [], "via": via,
        })

    direct = [(d, k, v) for d, entries in domains.items()
              for k, v in entries.items() if isinstance(v, dict) and matches(k, v)]
    for d, k, v in direct:
        emit(d, k, v, "direct")
    for d, k, v in direct:
        for rel in (v.get("related") or []):
            found = find_entry(str(rel))
            if found:
                emit(found[0], found[1], found[2], "related")
    return out[:max_entries]


def lookup(question, wiki_root=None, max_pages=15):
    root = wiki_root or find_wiki()
    if not root or not os.path.isdir(root):
        return {"no_wiki": True, "wiki_root": None,
                "message": "No .claude/wiki/ found by walking up from the current directory."}

    # Only the dig-deep schema is supported. A `.claude/wiki/` with none of the
    # structural markers (a `SCHEMA.md`, a `glossary/` dir, or a `pages/` dir) is
    # some other tool's / a hand-authored wiki — hand it off for direct reading
    # rather than silently mis-parsing it.
    is_digdeep = (os.path.isfile(os.path.join(root, "SCHEMA.md")) or
                  os.path.isdir(os.path.join(root, "glossary")) or
                  os.path.isdir(os.path.join(root, "pages")))
    if not is_digdeep:
        return {"no_wiki": True, "wiki_root": root, "foreign_wiki": True,
                "readable_directly": True,
                "message": ("Found .claude/wiki/ but not in dig-deep schema format — "
                            "the lane skips it; read it directly with Read/Grep.")}

    terms = _terms(question)
    result = {"no_wiki": False, "wiki_root": root, "terms": terms,
              "glossary": [], "relevant_pages": [], "contradictions": [], "gaps": []}

    # --- index.md: collect candidate pages (ranked by term/tag overlap) + tags ---
    index_path = os.path.join(root, "index.md")
    hit_tags, page_scores = set(), {}
    if os.path.isfile(index_path):
        with open(index_path, errors="replace") as f:
            for line in f:
                overlap = sum(1 for t in terms if t in line.lower())
                if not overlap:
                    continue
                line_tags = _TAG_RE.findall(line)
                hit_tags.update(line_tags)
                score = overlap + sum(1 for t in line_tags if t.lower() in terms)
                for m in _PAGE_RE.findall(line):
                    page_scores[m] = max(page_scores.get(m, 0), score)
    # strongest overlap first; ties keep first-seen order (dict insertion + stable sort)
    candidate_pages = sorted(page_scores, key=lambda m: page_scores[m], reverse=True)

    # --- glossary: structured subgraph (PyYAML) or substring fallback ---
    gloss_dir = os.path.join(root, "glossary")
    if os.path.isdir(gloss_dir) and terms:
        if _has_yaml():
            result["glossary"] = _glossary_subgraph(gloss_dir, terms)
        else:
            result["glossary"] = _glossary_substring(gloss_dir, terms, hit_tags)

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
