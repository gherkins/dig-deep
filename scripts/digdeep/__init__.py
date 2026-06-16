"""digdeep — framework-agnostic deep-research tools.

A small package of portable research "lanes" (web, Reddit, papers, YouTube,
wiki) that any agent — or a human at a shell — can drive. Each lane is a thin
wrapper over public, keyless endpoints (DuckDuckGo/Brave via `ddgs`, Reddit's
JSON API, OpenAlex/arXiv/Semantic Scholar/Crossref, and `yt-dlp`). Nothing is
hosted; every call runs locally on your machine.

The companion `AGENTS.md` spec explains how to orchestrate these lanes into a
full deep-research workflow from any agent framework.
"""

__version__ = "0.1.0"
