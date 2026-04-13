"""Tests for nekonote.ai (mocked HTTP)."""

from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

import pytest

from nekonote import ai
from nekonote.http import Response


class TestConfigure:
    def test_configure_stores_settings(self):
        ai.configure(provider="openai", api_key="sk-test", default_model="gpt-4o")
        assert ai._config["provider"] == "openai"
        assert ai._config["api_key"] == "sk-test"
        assert ai._config["default_model"] == "gpt-4o"

    def test_configure_with_base_url(self):
        ai.configure(provider="openai", api_key="k", base_url="https://custom.api/v1")
        assert ai._config["base_url"] == "https://custom.api/v1"


class TestGenerate:
    @patch("nekonote.ai._http_post")
    def test_openai_generate(self, mock_post):
        mock_post.return_value = Response(
            status_code=200,
            body=json.dumps({
                "choices": [{"message": {"content": "Hello from GPT"}}]
            }).encode(),
        )
        ai.configure(provider="openai", api_key="sk-test")
        result = ai.generate("Say hello")
        assert result == "Hello from GPT"
        mock_post.assert_called_once()

    @patch("nekonote.ai._http_post")
    def test_openai_with_system(self, mock_post):
        mock_post.return_value = Response(
            status_code=200,
            body=json.dumps({
                "choices": [{"message": {"content": "response"}}]
            }).encode(),
        )
        ai.configure(provider="openai", api_key="sk-test")
        ai.generate("prompt", system="You are helpful")
        # Check system message was included in the request body
        call_kwargs = mock_post.call_args
        req_json = call_kwargs[1]["json"]
        assert req_json["messages"][0]["role"] == "system"
        assert req_json["messages"][0]["content"] == "You are helpful"

    @patch("nekonote.ai._http_post")
    def test_gemini_generate(self, mock_post):
        mock_post.return_value = Response(
            status_code=200,
            body=json.dumps({
                "candidates": [{"content": {"parts": [{"text": "Hello from Gemini"}]}}]
            }).encode(),
        )
        result = ai.generate("Say hello", provider="gemini", api_key="gemini-key")
        assert result == "Hello from Gemini"

    @patch("nekonote.ai._http_post")
    def test_api_error(self, mock_post):
        mock_post.return_value = Response(status_code=500, body=b"Internal error")
        ai.configure(provider="openai", api_key="sk-test")
        with pytest.raises(RuntimeError, match="500"):
            ai.generate("test")

    def test_unsupported_provider(self):
        with pytest.raises(ValueError, match="Unsupported"):
            ai.generate("test", provider="unknown", api_key="k")


class TestGenerateJson:
    @patch("nekonote.ai._http_post")
    def test_json_output(self, mock_post):
        mock_post.return_value = Response(
            status_code=200,
            body=json.dumps({
                "choices": [{"message": {"content": '{"name": "Taro", "age": 25}'}}]
            }).encode(),
        )
        ai.configure(provider="openai", api_key="sk-test")
        result = ai.generate_json("Extract data")
        assert result["name"] == "Taro"
        assert result["age"] == 25

    @patch("nekonote.ai._http_post")
    def test_json_with_markdown_fence(self, mock_post):
        mock_post.return_value = Response(
            status_code=200,
            body=json.dumps({
                "choices": [{"message": {"content": '```json\n{"key": "value"}\n```'}}]
            }).encode(),
        )
        ai.configure(provider="openai", api_key="sk-test")
        result = ai.generate_json("Extract")
        assert result["key"] == "value"

    @patch("nekonote.ai._http_post")
    def test_json_with_schema(self, mock_post):
        mock_post.return_value = Response(
            status_code=200,
            body=json.dumps({
                "choices": [{"message": {"content": '{"invoice": "INV-001", "amount": 1000}'}}]
            }).encode(),
        )
        ai.configure(provider="openai", api_key="sk-test")
        schema = {"type": "object", "properties": {"invoice": {"type": "string"}}}
        result = ai.generate_json("Extract", schema=schema)
        assert result["invoice"] == "INV-001"
        # Check schema was passed in system message
        call_json = mock_post.call_args[1]["json"]
        sys_msg = call_json["messages"][0]["content"]
        assert "invoice" in sys_msg
