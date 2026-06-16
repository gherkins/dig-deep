#!/usr/bin/env python3
"""Lint adapter agent frontmatter (stdlib only — no YAML dependency).

Checks every adapters/*/agents/*.md file: has a terminated `---` frontmatter
block containing at least `name:` and `description:`. Exits non-zero on failure.
"""
import glob
import os
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..", "adapters")


def main():
    files = sorted(glob.glob(os.path.join(ROOT, "*", "agents", "*.md")))
    if not files:
        print("no adapter agent files found")
        return 1
    failed = False
    for path in files:
        with open(path) as f:
            text = f.read()
        rel = os.path.relpath(path, os.path.join(ROOT, ".."))
        if not text.startswith("---"):
            print("FAIL %s — no frontmatter" % rel)
            failed = True
            continue
        end = text.find("\n---", 3)
        if end == -1:
            print("FAIL %s — unterminated frontmatter" % rel)
            failed = True
            continue
        fm = text[3:end]
        missing = [k for k in ("name:", "description:") if k not in fm]
        if missing:
            print("FAIL %s — missing %s" % (rel, ", ".join(missing)))
            failed = True
        else:
            print("ok   %s" % rel)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
