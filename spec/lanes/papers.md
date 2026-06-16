# Lane: papers — academic literature

`digdeep papers` searches OpenAlex (250M+ works), arXiv (full text via ar5iv),
Semantic Scholar (citation graph + abstracts), and Crossref (DOI authority) — all
free and keyless. Use for cutting-edge or rigorous questions where blog posts and
docs fall short.

## Commands

```
digdeep papers search "query" [--sources openalex,arxiv,s2,crossref] [-n 25] \
    [--year-from 2022] [--min-citations 50] [--open-access]
digdeep papers read <arxiv-id | DOI | URL>
digdeep papers graph <id> [--direction citations|references|related] [--limit 25]
```

- **search** queries all sources in parallel, dedupes by DOI/title, and ranks by
  citation count. Returns `[{title, year, authors, doi, arxiv_id, oa_url, abstract, cited_by, sources}]`.
- **read** returns full text — ar5iv HTML for arXiv ids, the page for URLs, or
  S2 metadata + abstract + TL;DR for a bare DOI.
- **graph** walks the Semantic Scholar citation graph (papers citing this, its
  references, or AI-recommended related work).

## How to use it

1. **Search broad**, then triage by abstract / citation count.
2. **Read** the most relevant few — prefer ar5iv for arXiv papers (clean,
   always open, no fallback needed).
3. **Extract specific findings**, not paper lists. Cite `title + DOI/arXiv id`.
4. **Trace ideas** with `graph` when you need lineage (who built on this work).

## Tips

- **Citation counts are field- and age-relative.** A 2024 paper with 50 cites is
  impressive; a 2015 one with 50 is average. arXiv preprints report 0 here.
- **Cross-source agreement** (a paper on OpenAlex + S2 + Crossref) signals
  legitimacy; single-source hits deserve scrutiny.
- **Iterate on jargon** discovered in first results — academic terminology often
  differs from mainstream wording. Use `--year-from` / `--open-access` to narrow.
