from __future__ import annotations

import asyncio
import base64
from typing import Any

from nekonote.engine.context import ExecutionContext
from nekonote.engine.nodes.registry import register


def _get_browser_ctx(ctx: ExecutionContext):
    """Get or lazily initialize the Playwright browser context."""
    return ctx.variables.get("_browser_ctx")


def _get_page(ctx: ExecutionContext):
    """Get the current active page."""
    return ctx.variables.get("_browser_page")


@register("browser.open")
async def browser_open(params: dict[str, Any], ctx: ExecutionContext) -> Any:
    from playwright.async_api import async_playwright

    pw = await async_playwright().start()
    ctx.set("_playwright", pw)

    browser_type = params.get("browser_type", "chromium")
    headless = params.get("headless", False)

    launcher = getattr(pw, browser_type, pw.chromium)
    browser = await launcher.launch(headless=headless)
    browser_ctx = await browser.new_context()
    page = await browser_ctx.new_page()

    ctx.set("_browser", browser)
    ctx.set("_browser_ctx", browser_ctx)
    ctx.set("_browser_page", page)

    # Share with picker
    from nekonote.api.websocket import set_shared_page
    set_shared_page(page)

    return True


@register("browser.navigate")
async def browser_navigate(params: dict[str, Any], ctx: ExecutionContext) -> Any:
    page = _get_page(ctx)
    if not page:
        raise RuntimeError("No browser open. Use 'Open Browser' node first.")

    url = params.get("url", "")
    await page.goto(url, wait_until="domcontentloaded")
    ctx.set("_page_url", page.url)
    ctx.set("_page_title", await page.title())

    return page.url


@register("browser.click")
async def browser_click(params: dict[str, Any], ctx: ExecutionContext) -> Any:
    page = _get_page(ctx)
    if not page:
        raise RuntimeError("No browser open.")

    selector = params.get("selector", "")
    await page.click(selector)
    return True


@register("browser.type")
async def browser_type(params: dict[str, Any], ctx: ExecutionContext) -> Any:
    page = _get_page(ctx)
    if not page:
        raise RuntimeError("No browser open.")

    selector = params.get("selector", "")
    text = params.get("text", "")
    await page.fill(selector, text)
    return True


@register("browser.getText")
async def browser_get_text(params: dict[str, Any], ctx: ExecutionContext) -> Any:
    page = _get_page(ctx)
    if not page:
        raise RuntimeError("No browser open.")

    selector = params.get("selector", "")
    variable = params.get("variable", "")

    element = await page.query_selector(selector)
    if not element:
        raise RuntimeError(f"Element not found: {selector}")

    text = await element.text_content() or ""

    if variable:
        ctx.set(variable, text)

    return text


@register("browser.wait")
async def browser_wait(params: dict[str, Any], ctx: ExecutionContext) -> Any:
    page = _get_page(ctx)
    if not page:
        raise RuntimeError("No browser open.")

    selector = params.get("selector", "")
    timeout = int(params.get("timeout", 30000))
    await page.wait_for_selector(selector, timeout=timeout)
    return True


@register("browser.screenshot")
async def browser_screenshot(params: dict[str, Any], ctx: ExecutionContext) -> Any:
    page = _get_page(ctx)
    if not page:
        raise RuntimeError("No browser open.")

    path = params.get("path", "")

    if path:
        await page.screenshot(path=path)
        return path
    else:
        buf = await page.screenshot()
        encoded = base64.b64encode(buf).decode("ascii")
        return encoded


@register("browser.close")
async def browser_close(params: dict[str, Any], ctx: ExecutionContext) -> Any:
    browser = ctx.variables.get("_browser")
    pw = ctx.variables.get("_playwright")

    if browser:
        await browser.close()
        ctx.set("_browser", None)
        ctx.set("_browser_ctx", None)
        ctx.set("_browser_page", None)

    if pw:
        await pw.stop()
        ctx.set("_playwright", None)

    return True
