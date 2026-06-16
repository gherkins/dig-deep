# Lane: reddit — community opinion & experience

`digdeep reddit` uses Reddit's public JSON API to search threads and pull full
posts + nested comments. Best for product reviews from real users, niche
troubleshooting, honest opinions vs. marketing, and "what would you pick" calls.

## Commands

```
digdeep reddit search "query 1" "query 2" … [--subreddit X] [--time year] [--max 10]
digdeep reddit thread "/r/sub/comments/abc123/title/" [--comments 25]
```

- **search** runs queries (paced to respect rate limits), dedupes, and ranks
  candidates by `score + 2·num_comments`. Returns
  `{blocked, note, candidates: [{id, title, subreddit, score, num_comments, permalink, url}]}`.
- **thread** fetches one post + top comments (with up to depth-2 replies).
  Returns `{blocked, note, thread: {title, subreddit, author, score, selftext, comments[…]}}`.

## How to use it

1. **Search broadly** — 3–5 queries across angles; pick the 5–10 best threads
   (prefer 20+ comments and niche technical subs over generic ones).
2. **Fetch threads** for the top candidates.
3. **Quote with attribution**: `u/user in r/sub (score↑): "…"`. Reddit scores
   matter — a 500↑ comment outweighs a 3↑ one, but upvotes ≠ correctness.
4. **Synthesize**: group by sub-question, quantify consensus, flag disagreement,
   note recency (a 2021 thread may be stale for fast-moving topics).

## Tips

- **IP blocks are common.** When the JSON API returns `blocked: true` (a 403
  IP-level block on the `.json` path), backoff won't help. If the `[browser]`
  extra is installed, the lane returns rendered-HTML `raw_text` as a best-effort
  fallback; otherwise the `note` explains the block. This is environmental, not a
  bug — try from a different network or rely on `site:reddit.com` web hits.
- The lane already sends a descriptive User-Agent and paces requests (~2s) — both
  required to avoid instant 429/403.
