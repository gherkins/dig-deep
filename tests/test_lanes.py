import os

from digdeep.http import HttpResult
from digdeep.lanes import papers, playlist, reddit, wiki, youtube

FIX = os.path.join(os.path.dirname(__file__), "fixtures")


def test_papers_inverted_index():
    assert papers._abstract_from_inverted_index({"Hello": [0], "world": [1]}) == "Hello world"
    assert papers._abstract_from_inverted_index(None) is None


def test_papers_is_arxiv():
    assert papers._is_arxiv("1706.03762")
    assert papers._is_arxiv("2305.12345v2")
    assert not papers._is_arxiv("10.1145/3292500")
    assert not papers._is_arxiv("https://example.com")


def test_youtube_fmt_ts():
    assert youtube._fmt_ts(65) == "1:05"
    assert youtube._fmt_ts(3661) == "1:01:01"


def test_youtube_parse_json3():
    segs = youtube._parse_json3(os.path.join(FIX, "sample.json3"))
    texts = [s.text for s in segs]
    assert "Hello world" in texts
    assert segs[-1].ts == "1:01:01"
    assert len(segs) == 3   # the empty + segless events are dropped


def test_reddit_block_detection():
    assert reddit._is_blocked(HttpResult("u", 403, "<html>blocked</html>")) is True
    assert reddit._is_blocked(HttpResult("u", 200, '{"data":{}}')) is False


def test_reddit_parse_comment_filters():
    good = reddit._parse_comment({"body": "good point", "author": "alice", "score": 10, "replies": ""}, max_depth=2)
    assert good.author == "alice" and good.score == 10
    assert reddit._parse_comment({"body": "x", "author": "bob", "score": 1}, max_depth=2) is None      # low score
    assert reddit._parse_comment({"body": "x", "author": "[deleted]", "score": 9}, max_depth=2) is None  # deleted


def test_playlist_urlize_chunks_at_50():
    urls = playlist.urlize(["id%d" % i for i in range(120)], label="L")
    assert len(urls) == 3
    assert urls[0]["video_count"] == 50 and urls[2]["video_count"] == 20
    assert "part 1/3" in urls[0]["label"]


def test_wiki_lookup(tmp_path):
    root = tmp_path / ".claude" / "wiki"
    (root / "pages" / "llm").mkdir(parents=True)
    (root / "index.md").write_text("#llm #quant — [quantization](pages/llm/quant.md) — gguf vs exl2\n")
    (root / "pages" / "llm" / "quant.md").write_text(
        "---\ntitle: quantization\nconfidence: high\nlast_verified: 2026-06-16\n---\n\n"
        "## Summary\nGGUF is a container format for quantized weights.\n\n## Contradictions\nnone\n")
    res = wiki.lookup("what about quantization gguf", wiki_root=str(root))
    assert res["no_wiki"] is False
    assert any("quant.md" in p["path"] for p in res["relevant_pages"])


def test_wiki_no_wiki(tmp_path):
    assert wiki.lookup("anything", wiki_root=str(tmp_path / "nope"))["no_wiki"] is True
