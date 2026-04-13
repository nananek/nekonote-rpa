"""Tests for nekonote.config."""

from unittest.mock import patch

from nekonote import config


class TestConfig:
    @patch("nekonote.config._config_dir")
    def test_set_get(self, mock_dir, tmp_path):
        mock_dir.return_value = tmp_path
        config.set("browser", "firefox")
        assert config.get("browser") == "firefox"

    @patch("nekonote.config._config_dir")
    def test_get_default(self, mock_dir, tmp_path):
        mock_dir.return_value = tmp_path
        assert config.get("missing", "default_val") == "default_val"

    @patch("nekonote.config._config_dir")
    def test_get_all(self, mock_dir, tmp_path):
        mock_dir.return_value = tmp_path
        config.set("a", 1)
        config.set("b", 2)
        all_settings = config.get_all()
        assert all_settings["a"] == 1
        assert all_settings["b"] == 2


class TestCredentials:
    @patch("nekonote.config._config_dir")
    def test_set_get_credential(self, mock_dir, tmp_path):
        mock_dir.return_value = tmp_path
        config.set_credential("gmail", username="user", password="pass")
        cred = config.get_credential("gmail")
        assert cred["username"] == "user"
        assert cred["password"] == "pass"

    @patch("nekonote.config._config_dir")
    def test_list_credentials(self, mock_dir, tmp_path):
        mock_dir.return_value = tmp_path
        config.set_credential("a", key="1")
        config.set_credential("b", key="2")
        names = config.list_credentials()
        assert "a" in names
        assert "b" in names

    @patch("nekonote.config._config_dir")
    def test_get_missing_credential(self, mock_dir, tmp_path):
        mock_dir.return_value = tmp_path
        assert config.get_credential("nope") == {}


class TestEnv:
    def test_env_existing(self):
        import os
        os.environ["NEKONOTE_TEST_VAR"] = "hello"
        assert config.env("NEKONOTE_TEST_VAR") == "hello"
        del os.environ["NEKONOTE_TEST_VAR"]

    def test_env_missing(self):
        assert config.env("NONEXISTENT_VAR_12345", "fallback") == "fallback"
