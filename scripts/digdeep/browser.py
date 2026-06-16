"""Optional headless-browser fallback (Playwright).

Used only when an HTTP fetch looks blocked or sparse. Kept entirely optional:
if the `[browser]` extra (or the Chromium binary) is not installed, `render`
raises `BrowserUnavailable` and callers degrade gracefully to the HTTP result.

Nothing here is imported at package load time — `playwright` is imported lazily
so the core stays dependency-free.
"""
from __future__ import annotations

from .config import USER_AGENT


class BrowserUnavailable(RuntimeError):
    pass


def available() -> bool:
    try:
        import playwright.sync_api  # noqa: F401
        return True
    except Exception:
        return False


def render(url, wait_text=None, timeout_ms=20000) -> str:
    """Return the rendered visible text of a page. Raises BrowserUnavailable on any failure."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise BrowserUnavailable(
            "playwright not installed — `pip install 'digdeep[browser]' && playwright install chromium`"
        ) from e

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page(user_agent=USER_AGENT)
                page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
                if wait_text:
                    try:
                        page.get_by_text(wait_text).first.wait_for(timeout=8000)
                    except Exception:
                        pass
                try:
                    page.wait_for_load_state("networkidle", timeout=5000)
                except Exception:
                    pass
                return page.inner_text("body") or ""
            finally:
                browser.close()
    except BrowserUnavailable:
        raise
    except Exception as e:
        # Missing Chromium binary, navigation error, timeout, etc.
        raise BrowserUnavailable("browser render failed: %s" % e) from e
