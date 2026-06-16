# dig-deep

**Fire-and-forget deep research across the web, Reddit, YouTube, and academic
papers — as portable scripts any agent (or human) can drive.**

You ask one question; dig-deep casts a wide net, decides which sources matter,
digs each one, and synthesizes a single well-sourced answer. It started as a set
of [Claude Code](https://claude.com/claude-code) agents; this repo factors the
research logic into a framework-agnostic core so you can use it **anywhere**.

It's two things:

1. **`digdeep`** — a small Python CLI with one research *lane* per source. Each
   lane hits public, keyless endpoints (`ddgs`, Reddit's JSON API,
   OpenAlex/arXiv/Semantic Scholar/Crossref, `yt-dlp`). No API keys, no account,
   nothing hosted — every call runs locally on your machine.
2. **[`AGENTS.md`](AGENTS.md)** — a copy-and-customize spec that turns those
   lanes into a full orchestrated research workflow. Drop it into Claude Code,
   Cursor, Codex, Cline, a custom prompt loop — or just follow it yourself.

There's no server to run and no service to trust: you publish/clone *code*, and
it executes on the consumer's own box.

## The lanes

| Lane | Command | What it's for |
|------|---------|---------------|
| 🌐 Web | `digdeep web search\|fetch` | Broad meta-search (DuckDuckGo/Brave/Mojeek/Yandex) + full-page read |
| 💬 Reddit | `digdeep reddit search\|thread` | Real community opinion, product & troubleshooting experience |
| 📄 Papers | `digdeep papers search\|read\|graph` | Academic literature + citation graphs |
| ▶️ YouTube | `digdeep youtube` | Video transcripts + metadata |
| 📚 Wiki | `digdeep wiki` | Read-only "what do we already know?" over a local `.claude/wiki/` |
| 🎞️ Playlist | `digdeep playlist` | Bundle surfaced videos into one clickable playlist (presentation helper) |

## Quick start

```bash
pip install digdeep          # or: pipx install digdeep
digdeep doctor               # check which dependencies are present

# use a lane directly:
digdeep web search "best split keyboard 2026" "ergonomic keyboard RSI" -m 10
digdeep papers search "graph neural networks" --open-access -p
digdeep youtube "https://youtu.be/dQw4w9WgXcQ" --want transcript
digdeep reddit search "mechanical keyboard for wrist pain" --subreddit ErgoMechKeyboards
```

Every command prints JSON to stdout (pipe it to `jq`, or add `-p`/`--pretty`).

## Use it as a research *agent*

The lanes are the tools; [`AGENTS.md`](AGENTS.md) is the brain. It describes the
workflow — wiki prefetch → broad web sweep → route to the right lanes →
iterative fan-out → synthesize → (optionally) present videos as a playlist.

```
                 AGENTS.md  (orchestration spec — copy & customize)
                     │ drives
                     ▼
   ┌──────┬─────────┬────────┬─────────┬───────┬──────────┐
   │ web  │ reddit  │ papers │ youtube │ wiki  │ playlist │   ← digdeep CLI lanes
   └──────┴─────────┴────────┴─────────┴───────┴──────────┘
```

- **Claude Code** users: `pip install digdeep`, then copy the six agents into
  `~/.claude/agents/` for the full experience (parallel fan-out, the works) —
  see [`adapters/claude-code/`](adapters/claude-code/) for the exact commands.
- **Any other framework**: copy `AGENTS.md` into your agent's instructions, make
  sure `digdeep` is on PATH, and go. See [`docs/PORTABILITY.md`](docs/PORTABILITY.md).

## Dependencies

| Tool | Needed for | Install |
|------|-----------|---------|
| `python3` ≥ 3.9 | everything | — |
| `ddgs` | web lane | `pipx install ddgs` |
| `yt-dlp` | youtube + playlist lanes | `pip install yt-dlp` / `brew install yt-dlp` |
| `playwright` *(optional)* | blocked-page browser fallback | `pip install 'digdeep[browser]' && playwright install chromium` |
| `trafilatura` *(optional)* | better web text extraction | `pip install 'digdeep[extract]'` |

`digdeep doctor` reports exactly what's missing and how to fix it. The core
itself has **zero** required Python dependencies — it's stdlib plus those CLIs.

## Privacy & network

dig-deep talks directly to DuckDuckGo/Brave/Mojeek/Yandex (via `ddgs`), Reddit's
public JSON API, YouTube (via `yt-dlp`), and OpenAlex/arXiv/Semantic
Scholar/Crossref. There is **no central key, no proxy, and nothing hosted by
this project** — requests go from your machine to those public endpoints and
results stay local. (Reddit may IP-block its JSON API from some networks; the
lane detects this and degrades gracefully.)

## Repo layout

```
AGENTS.md            # the orchestration spec — the thing you copy & customize
scripts/digdeep/     # the portable core (lanes + CLI), one source of truth
spec/lanes/          # per-lane usage docs AGENTS.md references
adapters/            # framework adapters (claude-code/ is a complete worked example)
docs/                # PORTABILITY.md, wiki-SCHEMA.md
tests/               # fixture-based tests (no network)
```

## Contributing

New lanes and new framework adapters are the natural extension points — see
[`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

[MIT](LICENSE).
