"""Element picker: injects a highlight overlay into the Playwright page,
lets the user click an element, and returns a CSS selector."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Awaitable

logger = logging.getLogger(__name__)

PICKER_JS = """
(() => {
  if (window.__nekonote_picker) return;
  window.__nekonote_picker = true;

  const overlay = document.createElement('div');
  overlay.id = '__nekonote_overlay';
  overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;z-index:2147483646;pointer-events:none;';
  document.body.appendChild(overlay);

  const highlight = document.createElement('div');
  highlight.id = '__nekonote_highlight';
  highlight.style.cssText = 'position:fixed;border:2px solid #3b82f6;background:rgba(59,130,246,0.15);z-index:2147483647;pointer-events:none;transition:all 0.05s;display:none;';
  document.body.appendChild(highlight);

  const label = document.createElement('div');
  label.id = '__nekonote_label';
  label.style.cssText = 'position:fixed;z-index:2147483647;pointer-events:none;background:#1e293b;color:#e2e8f0;font:12px monospace;padding:2px 6px;border-radius:3px;display:none;white-space:nowrap;';
  document.body.appendChild(label);

  function getSelector(el) {
    // Try ID
    if (el.id) return '#' + CSS.escape(el.id);

    // Try unique attribute selectors
    for (const attr of ['data-testid', 'name', 'aria-label', 'placeholder', 'title', 'type']) {
      const val = el.getAttribute(attr);
      if (val) {
        const sel = el.tagName.toLowerCase() + '[' + attr + '="' + val.replace(/"/g, '\\\\"') + '"]';
        if (document.querySelectorAll(sel).length === 1) return sel;
      }
    }

    // Try tag + text content for buttons/links
    if (['A', 'BUTTON'].includes(el.tagName)) {
      const text = el.textContent?.trim().slice(0, 30);
      if (text) {
        const sel = el.tagName.toLowerCase() + ':has-text("' + text + '")';
        return sel;
      }
    }

    // Build path
    const parts = [];
    let current = el;
    while (current && current !== document.body) {
      let sel = current.tagName.toLowerCase();
      if (current.id) {
        parts.unshift('#' + CSS.escape(current.id));
        break;
      }
      if (current.className && typeof current.className === 'string') {
        const classes = current.className.trim().split(/\\s+/).filter(c => c && !c.startsWith('__'));
        if (classes.length > 0) {
          sel += '.' + classes.slice(0, 2).map(c => CSS.escape(c)).join('.');
        }
      }
      const parent = current.parentElement;
      if (parent) {
        const siblings = Array.from(parent.children).filter(c => c.tagName === current.tagName);
        if (siblings.length > 1) {
          const idx = siblings.indexOf(current) + 1;
          sel += ':nth-of-type(' + idx + ')';
        }
      }
      parts.unshift(sel);
      current = current.parentElement;
    }
    return parts.join(' > ');
  }

  function onMove(e) {
    const el = document.elementFromPoint(e.clientX, e.clientY);
    if (!el || el.id?.startsWith('__nekonote')) { highlight.style.display = 'none'; label.style.display = 'none'; return; }
    const rect = el.getBoundingClientRect();
    highlight.style.display = 'block';
    highlight.style.left = rect.left + 'px';
    highlight.style.top = rect.top + 'px';
    highlight.style.width = rect.width + 'px';
    highlight.style.height = rect.height + 'px';

    const sel = getSelector(el);
    label.style.display = 'block';
    label.textContent = sel;
    label.style.left = Math.min(rect.left, window.innerWidth - 300) + 'px';
    label.style.top = Math.max(0, rect.top - 24) + 'px';
  }

  function onClick(e) {
    e.preventDefault();
    e.stopPropagation();
    e.stopImmediatePropagation();
    const el = document.elementFromPoint(e.clientX, e.clientY);
    if (!el || el.id?.startsWith('__nekonote')) return;

    const selector = getSelector(el);
    const tagName = el.tagName.toLowerCase();
    const text = el.textContent?.trim().slice(0, 50) || '';

    // Clean up
    cleanup();

    // Report back
    window.__nekonote_picked = { selector, tagName, text };
  }

  function cleanup() {
    document.removeEventListener('mousemove', onMove, true);
    document.removeEventListener('click', onClick, true);
    document.removeEventListener('keydown', onKeydown, true);
    overlay.remove();
    highlight.remove();
    label.remove();
    window.__nekonote_picker = false;
  }

  function onKeydown(e) {
    if (e.key === 'Escape') {
      cleanup();
      window.__nekonote_picked = { selector: '', tagName: '', text: '', cancelled: true };
    }
  }

  document.addEventListener('mousemove', onMove, true);
  document.addEventListener('click', onClick, true);
  document.addEventListener('keydown', onKeydown, true);
})();
"""


async def start_picker(page) -> dict[str, str]:
    """Inject picker into the page and wait for user to click an element.
    Returns { selector, tagName, text } or { cancelled: true }."""

    # Inject picker script
    await page.evaluate(PICKER_JS)

    # Poll for result
    for _ in range(600):  # 60 seconds timeout
        result = await page.evaluate("window.__nekonote_picked || null")
        if result is not None:
            # Clean up
            await page.evaluate("delete window.__nekonote_picked; delete window.__nekonote_picker;")
            return result
        await asyncio.sleep(0.1)

    return {"selector": "", "tagName": "", "text": "", "cancelled": True, "timeout": True}
