# Contributing to dig-deep

Thanks for digging in. The two natural extension points are **new lanes** (a new
source type) and **new adapters** (a new agent framework).

## Dev setup

```bash
git clone https://github.com/gherkins/dig-deep && cd dig-deep
pip install -e '.[all]'      # editable install with optional extras
pip install pytest
digdeep doctor               # confirm ddgs / yt-dlp are present
pytest                       # tests are fixture-based and need no network
```

## Project shape

- `scripts/digdeep/` — the portable core. **One source of truth**: search/fetch/
  parse logic lives here and nowhere else.
  - `lanes/<name>.py` — one module per source. Public functions return
    dataclasses (`models.py`) or plain dicts; the CLI serializes them.
  - `cli.py` — argparse dispatch. `http.py` / `render.py` / `browser.py` —
    shared fetch + extraction. `merge.py` / `budgets.py` — helpers.
- `AGENTS.md` + `spec/lanes/` — the framework-neutral spec. Prose only; **no
  logic** that duplicates the core.
- `adapters/<framework>/` — thin renderings of `AGENTS.md` for one host.

## Adding a lane

1. Create `scripts/digdeep/lanes/<name>.py` with small, JSON-returning functions.
   Use `http.get`/`get_json` (stdlib, no `requests`) and `render.fetch_page` for
   web content; raise `errors.MissingTool` for any required external CLI.
2. Wire subcommands into `cli.py` (`parents=[common]` so `-p/--pretty` works).
3. Add it to `digdeep doctor` if it needs a new external tool.
4. Document usage in `spec/lanes/<name>.md` and add a row to the lane tables in
   `AGENTS.md` and `README.md`.
5. Add a fixture-based test in `tests/`.

## Adding an adapter

See [`docs/PORTABILITY.md`](docs/PORTABILITY.md). Copy `AGENTS.md`, wire the
`digdeep` calls into your framework, map Phase 3 to its concurrency model, and
drop the result in `adapters/<framework>/` with a short README.

## Conventions

- **No network in tests.** Use fixtures under `tests/fixtures/`.
- **Core stays dependency-light.** Required deps for the package itself: none.
  New heavyweight needs go in an optional extra (`[browser]`, `[extract]`, …).
- **Don't duplicate logic into prose.** If you find yourself writing Python in an
  agent `.md`, it belongs in a lane instead.
- **Adapter agent frontmatter** must parse as valid YAML with at least `name` and
  `description`; CI checks this.

## Before opening a PR

```bash
python -m py_compile $(find scripts -name '*.py')
pytest
```
