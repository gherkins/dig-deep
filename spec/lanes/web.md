# Lane: web — broad meta-search

`digdeep web` aggregates DuckDuckGo, Brave, Mojeek, Yandex (and others) through
the `ddgs` CLI. No API keys. Two steps, mirroring how a careful researcher works:
search broadly, then read the best pages.

## Commands

```
digdeep web search "query 1" "query 2" … [-m 10] [--backends brave,mojeek]
digdeep web fetch "https://…" "https://…" [--no-browser]
```

- **search** runs each query against a rotated backend in parallel, then dedupes
  by URL. Returns `[{title, url, snippet, backend, query}]`.
- **fetch** pulls full readable text per URL. Returns
  `[{url, status, text, via, blocked, note}]`. `via` is `"http"` or `"browser"`.

## How to use it

1. Run **5–8 queries** covering different angles — how it works, comparisons,
   gotchas/problems, official docs, alternatives, and a `site:reddit.com …` or
   `site:github.com …` probe. Breadth beats repetition.
2. Triage the merged hits by title/snippet; pick the **8–15** strongest URLs.
3. `fetch` them and read the full text — snippets are teasers, not answers.
4. Cite every non-trivial claim with its source URL.

## Tips

- **Rotate backends.** All queries on one engine trip its rate limit; spreading
  across `brave,duckduckgo,mojeek,yandex` keeps each under threshold. `google` is
  intentionally excluded (frequently rate-limited).
- **Blocked pages.** If a fetch comes back `blocked: true` / sparse, and the
  optional `[browser]` extra is installed, `fetch` automatically retries through
  a headless browser (`via: "browser"`). Without it, you get the HTTP result plus
  a note — still usable, just thinner.
- **Reddit URLs** fetch poorly here; use the dedicated `reddit` lane for depth.
