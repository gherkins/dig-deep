from digdeep import budgets, merge, models, render
from digdeep.models import Paper


def test_dedupe_keeps_first():
    items = [{"u": "a"}, {"u": "b"}, {"u": "a"}]
    assert [i["u"] for i in merge.dedupe(items, key=lambda x: x["u"])] == ["a", "b"]


def test_normalize_url_equates_scheme_www_slash():
    assert merge.normalize_url("https://www.Example.com/x/") == merge.normalize_url("http://example.com/x")


def test_rank_desc():
    assert merge.rank([1, 3, 2], score=lambda x: x) == [3, 2, 1]


def test_budget_classify_and_get():
    assert budgets.classify("give it a quick dive").name == "quick"
    assert budgets.classify("tell me about widgets").name == "deep"   # default
    assert budgets.get_profile("standard").rounds_per_lane == 2


def test_to_jsonable_dataclass_and_set():
    d = models.to_jsonable(Paper(title="t", sources=["S2", "arXiv"]))
    assert d["title"] == "t" and d["sources"] == ["S2", "arXiv"]
    assert models.to_jsonable({"s": {3, 1, 2}}) == {"s": [1, 2, 3]}


def test_html_to_text_strips_script_style():
    html = ("<html><head><style>x{}</style></head><body>"
            "<p>Hello</p><script>bad()</script><p>World</p></body></html>")
    txt = render.html_to_text(html)
    assert "Hello" in txt and "World" in txt and "bad()" not in txt


def test_looks_blocked():
    assert render.looks_blocked("", 200) is True            # sparse
    assert render.looks_blocked("x" * 600, 403) is True     # error status
    assert render.looks_blocked("x" * 600, 200) is False    # fine


def test_normalize_url_strips_tracking_and_fragment():
    base = merge.normalize_url("https://example.com/post")
    assert merge.normalize_url("https://example.com/post?utm_source=tw&utm_medium=x") == base
    assert merge.normalize_url("https://example.com/post#section") == base
    assert merge.normalize_url("https://example.com/post?fbclid=123&ref=hn") == base


def test_normalize_url_keeps_meaningful_query_distinct():
    # distinct ?v= must NOT collapse together (the over-merge guard)
    assert merge.normalize_url("https://youtube.com/watch?v=AAA") != \
        merge.normalize_url("https://youtube.com/watch?v=BBB")
    # param order doesn't matter (sorted key)
    assert merge.normalize_url("https://e.com/x?a=1&b=2") == merge.normalize_url("https://e.com/x?b=2&a=1")


def test_budget_classify_minutes():
    assert budgets.classify_minutes(5).name == "quick"
    assert budgets.classify_minutes(6).name == "quick"
    assert budgets.classify_minutes(7).name == "standard"
    assert budgets.classify_minutes(14).name == "standard"
    assert budgets.classify_minutes(15).name == "deep"
    assert budgets.classify_minutes("not a number").name == "deep"   # fallback


def test_standard_soft_minutes_reconciled():
    assert budgets.get_profile("standard").soft_minutes == 10
