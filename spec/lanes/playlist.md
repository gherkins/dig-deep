# Lane: playlist — present videos as a clickable playlist

`digdeep playlist` is a **results-presentation helper**, not a research lane. When
a dig surfaces YouTube videos worth watching, bundle them into a single
`watch_videos` URL the user opens and saves with one click — no Data API, no
OAuth, no quota.

## Commands

```
digdeep playlist urlize <id1> <id2> … [--label "dig-deep: topic"]   # IDs you already have
digdeep playlist search "title channel" [--top 3]                   # resolve one reference
digdeep playlist resolve refs.json [--top 1]                        # batch-resolve references
```

- **urlize** turns video IDs into `watch_videos` URLs, chunked at 50 IDs (YouTube's
  hard cap). Returns `[{url, video_count, label?}]`.
- **search** / **resolve** turn free-text references into video IDs via `yt-dlp`
  when the report mentions titles rather than IDs. `resolve` takes a JSON list of
  `{"id": "...", "query": "..."}` and resolves them in parallel, tagging each with
  a `status` (`ok`, `search_empty`, `timeout`, …).

## How to use it (as a closing step in a dig)

1. Collect the videos the research actually cited (from the `youtube` lane or web
   hits). If you have their IDs, go straight to `urlize`.
2. If you only have titles, write them to `refs.json` and `resolve` first, then
   `urlize` the resulting `video_id`s.
3. Hand the user the `watch_videos` URL(s) at the end of the report: "Here's a
   playlist of the videos referenced above — open it and hit Save."

## Tips

- This is opt-in flavor. Only build a playlist when there are genuinely several
  videos worth watching; a single cited video doesn't need one.
- `urlize` needs no network or external tools; `search`/`resolve` need `yt-dlp`.
