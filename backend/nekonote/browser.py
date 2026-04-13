"""Synchronous browser automation API for nekonote scripts.

Usage::

    from nekonote import browser

    browser.open()
    browser.navigate("https://example.com")
    browser.click("#submit")
    text = browser.get_text("h1")
    browser.close()
"""

from __future__ import annotations

import base64
from typing import Any, Literal

from nekonote._runtime import register_cleanup, run_async
from nekonote.errors import BrowserNotOpenError, ElementNotFoundError, TimeoutError

# ---------------------------------------------------------------------------
# Internal state
# ---------------------------------------------------------------------------

_pw: Any = None
_browser: Any = None
_context: Any = None
_page: Any = None


def _require_page(action: str = ""):
    if _page is None:
        raise BrowserNotOpenError(action=action)
    return _page


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def open(
    browser_type: Literal["chromium", "firefox", "webkit"] = "chromium",
    headless: bool = False,
) -> None:
    """Launch a browser instance."""
    global _pw, _browser, _context, _page

    async def _open():
        global _pw, _browser, _context, _page
        from playwright.async_api import async_playwright

        _pw = await async_playwright().start()
        launcher = getattr(_pw, browser_type, _pw.chromium)
        _browser = await launcher.launch(headless=headless)
        _context = await _browser.new_context()
        _page = await _context.new_page()

    run_async(_open())
    register_cleanup(_async_close)


def navigate(url: str) -> str:
    """Navigate to *url* and return the final URL."""
    page = _require_page("browser.navigate")

    async def _nav():
        await page.goto(url, wait_until="domcontentloaded")
        return page.url

    return run_async(_nav())


def click(selector: str, *, timeout: float = 5000) -> None:
    """Click the element matching *selector*."""
    page = _require_page("browser.click")

    async def _click():
        try:
            await page.click(selector, timeout=timeout)
        except Exception as e:
            err_msg = str(e)
            if "waiting for locator" in err_msg.lower() or "timeout" in err_msg.lower():
                # Gather available elements for suggestion
                similar = await _find_similar_selectors(page, selector)
                ctx: dict[str, Any] = {
                    "selector": selector,
                    "page_url": page.url,
                    "page_title": await page.title(),
                }
                suggestion = ""
                if similar:
                    ctx["similar_selectors"] = similar
                    suggestion = f"Similar selectors found: {', '.join(similar[:5])}"
                raise ElementNotFoundError(
                    f"Selector '{selector}' matched 0 elements on {page.url}",
                    action="browser.click",
                    context=ctx,
                    suggestion=suggestion,
                ) from None
            raise

    run_async(_click())


def type(selector: str, text: str, *, clear: bool = True, timeout: float = 5000) -> None:
    """Type *text* into the element matching *selector*."""
    page = _require_page("browser.type")

    async def _type():
        try:
            if clear:
                await page.fill(selector, text, timeout=timeout)
            else:
                await page.locator(selector).press_sequentially(text, timeout=timeout)
        except Exception as e:
            if "waiting for locator" in str(e).lower() or "timeout" in str(e).lower():
                similar = await _find_similar_selectors(page, selector, kind="input")
                raise ElementNotFoundError(
                    f"Input '{selector}' not found on {page.url}",
                    action="browser.type",
                    context={
                        "selector": selector,
                        "page_url": page.url,
                        "similar_selectors": similar,
                    },
                    suggestion=f"Available inputs: {', '.join(similar[:5])}" if similar else "",
                ) from None
            raise

    run_async(_type())


def get_text(selector: str, *, timeout: float = 5000) -> str:
    """Return the text content of the element matching *selector*."""
    page = _require_page("browser.get_text")

    async def _get():
        el = await page.query_selector(selector)
        if not el:
            similar = await _find_similar_selectors(page, selector)
            raise ElementNotFoundError(
                f"Selector '{selector}' not found on {page.url}",
                action="browser.get_text",
                context={
                    "selector": selector,
                    "page_url": page.url,
                    "similar_selectors": similar,
                },
                suggestion=f"Similar: {', '.join(similar[:5])}" if similar else "",
            )
        return await el.text_content() or ""

    return run_async(_get())


def get_attribute(selector: str, attribute: str) -> str | None:
    """Return an attribute value of the element matching *selector*."""
    page = _require_page("browser.get_attribute")

    async def _get():
        el = await page.query_selector(selector)
        if not el:
            raise ElementNotFoundError(
                f"Selector '{selector}' not found",
                action="browser.get_attribute",
            )
        return await el.get_attribute(attribute)

    return run_async(_get())


def get_html(selector: str) -> str:
    """Return the innerHTML of the element matching *selector*."""
    page = _require_page("browser.get_html")

    async def _get():
        return await page.eval_on_selector(selector, "el => el.innerHTML")

    return run_async(_get())


def wait(selector: str, *, timeout: float = 30000) -> None:
    """Wait for *selector* to appear on the page."""
    page = _require_page("browser.wait")

    async def _wait():
        try:
            await page.wait_for_selector(selector, timeout=timeout)
        except Exception:
            raise TimeoutError(
                f"Timed out after {timeout}ms waiting for '{selector}'",
                action="browser.wait",
                context={"selector": selector, "timeout_ms": timeout, "page_url": page.url},
                suggestion="Increase timeout or check if the selector is correct.",
            ) from None

    run_async(_wait())


def screenshot(path: str = "") -> str:
    """Take a screenshot.  Returns base64 string if *path* is empty."""
    page = _require_page("browser.screenshot")

    async def _shot():
        if path:
            await page.screenshot(path=path)
            return path
        buf = await page.screenshot()
        return base64.b64encode(buf).decode("ascii")

    return run_async(_shot())


def execute_js(expression: str) -> Any:
    """Execute JavaScript on the page and return the result."""
    page = _require_page("browser.execute_js")
    return run_async(page.evaluate(expression))


def is_visible(selector: str) -> bool:
    """Check if an element is visible."""
    page = _require_page("browser.is_visible")
    return run_async(page.is_visible(selector))


def count(selector: str) -> int:
    """Return the number of elements matching *selector*."""
    page = _require_page("browser.count")

    async def _count():
        return await page.eval_on_selector_all(selector, "els => els.length")

    return run_async(_count())


def select(selector: str, *, value: str = "", label: str = "", index: int | None = None) -> None:
    """Select an option in a <select> element."""
    page = _require_page("browser.select")

    async def _select():
        if value:
            await page.select_option(selector, value=value)
        elif label:
            await page.select_option(selector, label=label)
        elif index is not None:
            await page.select_option(selector, index=index)

    run_async(_select())


def check(selector: str) -> None:
    """Check a checkbox."""
    page = _require_page("browser.check")
    run_async(page.check(selector))


def uncheck(selector: str) -> None:
    """Uncheck a checkbox."""
    page = _require_page("browser.uncheck")
    run_async(page.uncheck(selector))


def scroll(selector: str = "", *, direction: str = "down", amount: int = 500) -> None:
    """Scroll the page or a specific element."""
    page = _require_page("browser.scroll")

    async def _scroll():
        delta_x = 0
        delta_y = amount if direction == "down" else -amount
        if direction == "right":
            delta_x, delta_y = amount, 0
        elif direction == "left":
            delta_x, delta_y = -amount, 0

        if selector:
            await page.eval_on_selector(
                selector,
                f"el => el.scrollBy({delta_x}, {delta_y})",
            )
        else:
            await page.mouse.wheel(delta_x, delta_y)

    run_async(_scroll())


def back() -> None:
    """Go back in history."""
    page = _require_page("browser.back")
    run_async(page.go_back())


def forward() -> None:
    """Go forward in history."""
    page = _require_page("browser.forward")
    run_async(page.go_forward())


def reload() -> None:
    """Reload the page."""
    page = _require_page("browser.reload")
    run_async(page.reload())


def new_tab(url: str = "") -> None:
    """Open a new tab, optionally navigating to *url*."""
    global _page
    ctx = _context
    if ctx is None:
        raise BrowserNotOpenError(action="browser.new_tab")

    async def _new():
        global _page
        _page = await ctx.new_page()
        if url:
            await _page.goto(url, wait_until="domcontentloaded")

    run_async(_new())


def get_tabs() -> list[dict[str, str]]:
    """Return info about all open tabs."""
    ctx = _context
    if ctx is None:
        return []

    async def _tabs():
        pages = ctx.pages
        result = []
        for i, p in enumerate(pages):
            result.append({"index": i, "url": p.url, "title": await p.title()})
        return result

    return run_async(_tabs())


def switch_tab(index: int) -> None:
    """Switch to the tab at *index*."""
    global _page
    ctx = _context
    if ctx is None:
        raise BrowserNotOpenError(action="browser.switch_tab")

    async def _switch():
        global _page
        pages = ctx.pages
        if 0 <= index < len(pages):
            _page = pages[index]
            await _page.bring_to_front()
        else:
            raise IndexError(f"Tab index {index} out of range (0..{len(pages) - 1})")

    run_async(_switch())


def close_tab() -> None:
    """Close the current tab and switch to the previous one."""
    global _page
    ctx = _context
    if ctx is None:
        return

    async def _close():
        global _page
        await _page.close()
        pages = ctx.pages
        if pages:
            _page = pages[-1]
            await _page.bring_to_front()
        else:
            _page = None

    run_async(_close())


def upload(selector: str, file_path: str) -> None:
    """Upload a file to a file input element."""
    page = _require_page("browser.upload")
    run_async(page.set_input_files(selector, file_path))


def get_table(selector: str) -> list[dict[str, str]]:
    """Extract a table as a list of dicts (header row becomes keys)."""
    page = _require_page("browser.get_table")

    js = """
    (selector) => {
        const table = document.querySelector(selector);
        if (!table) return null;
        const rows = Array.from(table.querySelectorAll('tr'));
        if (rows.length < 2) return [];
        const headers = Array.from(rows[0].querySelectorAll('th, td')).map(c => c.textContent.trim());
        return rows.slice(1).map(row => {
            const cells = Array.from(row.querySelectorAll('td, th')).map(c => c.textContent.trim());
            const obj = {};
            headers.forEach((h, i) => { obj[h] = cells[i] || ''; });
            return obj;
        });
    }
    """

    async def _get():
        result = await page.evaluate(js, selector)
        if result is None:
            raise ElementNotFoundError(
                f"Table '{selector}' not found",
                action="browser.get_table",
                context={"selector": selector, "page_url": page.url},
            )
        return result

    return run_async(_get())


def get_page_info() -> dict[str, Any]:
    """Return current page info (useful for AI inspect)."""
    page = _require_page("browser.get_page_info")

    js = """
    () => {
        const info = {
            url: location.href,
            title: document.title,
            clickable: [],
            inputs: [],
            tables: [],
        };
        document.querySelectorAll('a, button, [role="button"], [onclick]').forEach(el => {
            const sel = el.id ? '#' + el.id : el.tagName.toLowerCase() +
                (el.className ? '.' + el.className.split(' ').filter(Boolean).join('.') : '');
            info.clickable.push({
                selector: sel,
                tag: el.tagName.toLowerCase(),
                text: (el.textContent || '').trim().substring(0, 80),
                visible: el.offsetParent !== null,
            });
        });
        document.querySelectorAll('input, textarea, select').forEach(el => {
            const sel = el.id ? '#' + el.id : (el.name ? `[name="${el.name}"]` : el.tagName.toLowerCase());
            info.inputs.push({
                selector: sel,
                type: el.type || el.tagName.toLowerCase(),
                placeholder: el.placeholder || '',
                value: el.value || '',
            });
        });
        document.querySelectorAll('table').forEach((tbl, i) => {
            const sel = tbl.id ? '#' + tbl.id : `table:nth-of-type(${i + 1})`;
            const rows = tbl.querySelectorAll('tr');
            const headers = rows.length > 0
                ? Array.from(rows[0].querySelectorAll('th, td')).map(c => c.textContent.trim())
                : [];
            info.tables.push({ selector: sel, rows: rows.length, headers });
        });
        return info;
    }
    """

    return run_async(page.evaluate(js))


def accept_dialog(prompt_text: str = "") -> None:
    """Accept the next dialog (alert, confirm, prompt)."""
    page = _require_page("browser.accept_dialog")

    async def _accept():
        async def handler(dialog):
            await dialog.accept(prompt_text)

        page.once("dialog", handler)

    run_async(_accept())


def dismiss_dialog() -> None:
    """Dismiss the next dialog."""
    page = _require_page("browser.dismiss_dialog")

    async def _dismiss():
        async def handler(dialog):
            await dialog.dismiss()

        page.once("dialog", handler)

    run_async(_dismiss())


def close() -> None:
    """Close the browser."""
    run_async(_async_close())


async def _async_close() -> None:
    global _pw, _browser, _context, _page
    if _browser:
        try:
            await _browser.close()
        except Exception:
            pass
        _browser = None
        _context = None
        _page = None
    if _pw:
        try:
            await _pw.stop()
        except Exception:
            pass
        _pw = None


# ---------------------------------------------------------------------------
# Helpers for enriched error messages
# ---------------------------------------------------------------------------


async def _find_similar_selectors(page, selector: str, kind: str = "") -> list[str]:
    """Return a list of existing selectors that might be what the user meant."""
    try:
        if kind == "input":
            js = """
            () => Array.from(document.querySelectorAll('input, textarea, select')).slice(0, 20).map(el =>
                el.id ? '#' + el.id : (el.name ? '[name=\"' + el.name + '\"]' : el.tagName.toLowerCase())
            )
            """
        else:
            js = """
            () => Array.from(document.querySelectorAll('a, button, input, [id], [role="button"]')).slice(0, 30).map(el =>
                el.id ? '#' + el.id : el.tagName.toLowerCase() + (el.className ? '.' + String(el.className).split(' ').filter(Boolean)[0] : '')
            )
            """
        return await page.evaluate(js)
    except Exception:
        return []
