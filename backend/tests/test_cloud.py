"""Tests for cloud integrations (teams, gsheets)."""

from unittest.mock import patch, MagicMock

from nekonote import teams
from nekonote.http import Response


class TestTeams:
    @patch("nekonote.teams._http_post")
    def test_post_webhook(self, mock_post):
        mock_post.return_value = Response(status_code=200, body=b"1")
        teams.post_webhook(webhook_url="https://test.webhook", message="Hello")
        mock_post.assert_called_once()
        call_json = mock_post.call_args[1]["json"]
        assert "Hello" in str(call_json)

    @patch("nekonote.teams._http_post")
    def test_post_webhook_with_title(self, mock_post):
        mock_post.return_value = Response(status_code=200, body=b"1")
        teams.post_webhook(webhook_url="https://test", message="Body", title="Title")
        call_json = mock_post.call_args[1]["json"]
        assert call_json["sections"][0]["activityTitle"] == "Title"

    @patch("nekonote.teams._http_post")
    def test_webhook_error(self, mock_post):
        mock_post.return_value = Response(status_code=500, body=b"error")
        try:
            teams.post_webhook(webhook_url="https://test", message="x")
            assert False
        except RuntimeError as e:
            assert "500" in str(e)
