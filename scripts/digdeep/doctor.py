"""`digdeep doctor` — check which dependencies are installed and how to get the rest."""
from __future__ import annotations

import shutil
import sys


def _has_cmd(name):
    return shutil.which(name) is not None


def _has_module(mod):
    try:
        __import__(mod)
        return True
    except Exception:
        return False


def _has_chromium():
    """Playwright module present AND a Chromium build installed."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            path = p.chromium.executable_path
            import os
            return bool(path) and os.path.exists(path)
    except Exception:
        return False


def check():
    """Return (rows, all_required_ok). Each row: (name, present, required, hint)."""
    rows = [
        ("python3", True, True, sys.version.split()[0]),
        ("ddgs", _has_cmd("ddgs"), True, "pipx install ddgs   (web lane)"),
        ("yt-dlp", _has_cmd("yt-dlp"), True, "pip install yt-dlp   (youtube + playlist lanes)"),
        ("trafilatura", _has_module("trafilatura"), False, "pip install 'digdeep[extract]'   (better web extraction)"),
        ("playwright", _has_module("playwright"), False, "pip install 'digdeep[browser]'   (browser fallback)"),
        ("PyYAML", _has_module("yaml"), False, "pip install 'digdeep[wiki]'   (structured wiki glossary traversal)"),
    ]
    if _has_module("playwright"):
        rows.append(("chromium", _has_chromium(), False, "playwright install chromium   (browser fallback)"))
    all_required_ok = all(present for _, present, required, _ in rows if required)
    return rows, all_required_ok


def render_table(rows):
    lines = ["", "digdeep doctor — dependency check", "=" * 56]
    for name, present, required, hint in rows:
        mark = "OK  " if present else "MISS"
        tag = "required" if required else "optional"
        lines.append("[%s] %-12s (%s)" % (mark, name, tag))
        if not present:
            lines.append("       → %s" % hint)
    lines.append("=" * 56)
    return "\n".join(lines)


def main():
    rows, ok = check()
    print(render_table(rows))
    if ok:
        print("All required tools present. You're good to dig.\n")
    else:
        print("Some required tools are missing — install them with the commands above.\n")
    return 0 if ok else 1
