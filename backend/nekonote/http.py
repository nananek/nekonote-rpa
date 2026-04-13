"""HTTP/REST API request module for nekonote scripts.

Usage::

    from nekonote import http

    resp = http.get("https://api.example.com/users")
    data = resp.json()

    resp = http.post("https://api.example.com/users", json={"name": "Taro"})
"""

from __future__ import annotations

import json as _json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass
class Response:
    """Simple HTTP response wrapper."""

    status_code: int
    body: bytes
    headers: dict[str, str] = field(default_factory=dict)

    def text(self, encoding: str = "utf-8") -> str:
        return self.body.decode(encoding)

    def json(self) -> Any:
        return _json.loads(self.body)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get(url: str, *, headers: dict[str, str] | None = None, params: dict[str, str] | None = None) -> Response:
    """Send a GET request."""
    if params:
        from urllib.parse import urlencode

        url = url + ("&" if "?" in url else "?") + urlencode(params)
    return _request("GET", url, headers=headers)


def post(
    url: str,
    *,
    json: Any | None = None,
    data: bytes | str | None = None,
    headers: dict[str, str] | None = None,
) -> Response:
    """Send a POST request."""
    return _request("POST", url, json=json, data=data, headers=headers)


def put(
    url: str,
    *,
    json: Any | None = None,
    data: bytes | str | None = None,
    headers: dict[str, str] | None = None,
) -> Response:
    """Send a PUT request."""
    return _request("PUT", url, json=json, data=data, headers=headers)


def patch(
    url: str,
    *,
    json: Any | None = None,
    data: bytes | str | None = None,
    headers: dict[str, str] | None = None,
) -> Response:
    """Send a PATCH request."""
    return _request("PATCH", url, json=json, data=data, headers=headers)


def delete(url: str, *, headers: dict[str, str] | None = None) -> Response:
    """Send a DELETE request."""
    return _request("DELETE", url, headers=headers)


def download(url: str, save_to: str, *, headers: dict[str, str] | None = None) -> str:
    """Download a file from *url* to *save_to*. Returns the saved path."""
    Path(save_to).parent.mkdir(parents=True, exist_ok=True)
    req = Request(url, method="GET")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    with urlopen(req) as resp, open(save_to, "wb") as f:
        shutil.copyfileobj(resp, f)
    return str(Path(save_to).resolve())


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------


def _request(
    method: str,
    url: str,
    *,
    json: Any | None = None,
    data: bytes | str | None = None,
    headers: dict[str, str] | None = None,
) -> Response:
    hdrs = dict(headers or {})
    body: bytes | None = None

    if json is not None:
        body = _json.dumps(json, ensure_ascii=False).encode("utf-8")
        hdrs.setdefault("Content-Type", "application/json; charset=utf-8")
    elif data is not None:
        body = data.encode("utf-8") if isinstance(data, str) else data

    req = Request(url, data=body, method=method)
    for k, v in hdrs.items():
        req.add_header(k, v)

    try:
        with urlopen(req) as resp:
            resp_body = resp.read()
            resp_headers = {k: v for k, v in resp.getheaders()}
            return Response(
                status_code=resp.status,
                body=resp_body,
                headers=resp_headers,
            )
    except HTTPError as e:
        resp_body = e.read()
        return Response(
            status_code=e.code,
            body=resp_body,
            headers={k: v for k, v in e.headers.items()},
        )
