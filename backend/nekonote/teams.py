"""Microsoft Teams integration for nekonote scripts.

Usage::

    from nekonote import teams

    teams.post_webhook(webhook_url="https://...", message="RPA done!")
"""

from __future__ import annotations

from nekonote.http import post as _http_post


def post_webhook(
    *,
    webhook_url: str,
    message: str,
    title: str = "",
) -> None:
    """Post a message to a Teams channel via Incoming Webhook."""
    card = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "summary": title or message[:50],
        "themeColor": "7c3aed",
        "sections": [
            {
                "activityTitle": title,
                "text": message,
            }
        ] if title else [],
        "text": message if not title else "",
    }
    resp = _http_post(webhook_url, json=card)
    if resp.status_code not in (200, 202):
        raise RuntimeError(f"Teams webhook failed ({resp.status_code}): {resp.text()}")
