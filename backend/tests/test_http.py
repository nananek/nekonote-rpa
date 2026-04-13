"""Tests for nekonote.http (mocked urllib)."""

from __future__ import annotations

import json
from io import BytesIO
from unittest.mock import MagicMock, patch

from nekonote import http
from nekonote.http import Response


class TestResponse:
    def test_text(self):
        r = Response(status_code=200, body=b"hello")
        assert r.text() == "hello"

    def test_json(self):
        r = Response(status_code=200, body=b'{"key": "value"}')
        assert r.json() == {"key": "value"}

    def test_status_code(self):
        r = Response(status_code=404, body=b"not found")
        assert r.status_code == 404


def _mock_response(body: bytes, status: int = 200, headers: list | None = None):
    resp = MagicMock()
    resp.read.return_value = body
    resp.status = status
    resp.getheaders.return_value = headers or [("Content-Type", "application/json")]
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=False)
    return resp


class TestGet:
    @patch("nekonote.http.urlopen")
    def test_get_json(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(b'{"users": []}')
        resp = http.get("https://api.example.com/users")
        assert resp.status_code == 200
        assert resp.json() == {"users": []}

    @patch("nekonote.http.urlopen")
    def test_get_with_params(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(b"ok")
        http.get("https://api.example.com/search", params={"q": "test"})
        call_args = mock_urlopen.call_args[0][0]
        assert "q=test" in call_args.full_url

    @patch("nekonote.http.urlopen")
    def test_get_with_headers(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(b"ok")
        http.get("https://api.example.com/", headers={"Authorization": "Bearer xxx"})
        call_args = mock_urlopen.call_args[0][0]
        assert call_args.get_header("Authorization") == "Bearer xxx"


class TestPost:
    @patch("nekonote.http.urlopen")
    def test_post_json(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(b'{"id": 1}', 201)
        resp = http.post(
            "https://api.example.com/users",
            json={"name": "Taro"},
        )
        assert resp.status_code == 201
        call_args = mock_urlopen.call_args[0][0]
        assert call_args.method == "POST"
        assert b"Taro" in call_args.data

    @patch("nekonote.http.urlopen")
    def test_post_raw_data(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(b"ok")
        http.post("https://example.com", data="raw body")
        call_args = mock_urlopen.call_args[0][0]
        assert call_args.data == b"raw body"


class TestOtherMethods:
    @patch("nekonote.http.urlopen")
    def test_put(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(b"ok")
        resp = http.put("https://example.com/1", json={"name": "updated"})
        call_args = mock_urlopen.call_args[0][0]
        assert call_args.method == "PUT"

    @patch("nekonote.http.urlopen")
    def test_patch(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(b"ok")
        http.patch("https://example.com/1", json={"name": "patched"})
        call_args = mock_urlopen.call_args[0][0]
        assert call_args.method == "PATCH"

    @patch("nekonote.http.urlopen")
    def test_delete(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(b"ok")
        http.delete("https://example.com/1")
        call_args = mock_urlopen.call_args[0][0]
        assert call_args.method == "DELETE"


class TestErrorHandling:
    @patch("nekonote.http.urlopen")
    def test_http_error_returns_response(self, mock_urlopen):
        from urllib.error import HTTPError

        error = HTTPError(
            "https://example.com", 404, "Not Found", {"Content-Type": "text/plain"}, BytesIO(b"not found")
        )
        mock_urlopen.side_effect = error
        resp = http.get("https://example.com")
        assert resp.status_code == 404
        assert resp.text() == "not found"
