"""Tests for nekonote.scheduler."""

from unittest.mock import patch

from nekonote import scheduler


class TestScheduler:
    @patch("nekonote.scheduler._jobs_path")
    def test_add_list_remove(self, mock_path, tmp_path):
        mock_path.return_value = tmp_path / "schedules.json"

        scheduler.add("test_job", cron="0 9 * * *", script="report.py")
        jobs = scheduler.list()
        assert "test_job" in jobs
        assert jobs["test_job"]["cron"] == "0 9 * * *"
        assert jobs["test_job"]["enabled"] is True

        scheduler.remove("test_job")
        assert "test_job" not in scheduler.list()

    @patch("nekonote.scheduler._jobs_path")
    def test_enable_disable(self, mock_path, tmp_path):
        mock_path.return_value = tmp_path / "schedules.json"

        scheduler.add("j", cron="*/5 * * * *", script="check.py")
        scheduler.disable("j")
        assert scheduler.list()["j"]["enabled"] is False

        scheduler.enable("j")
        assert scheduler.list()["j"]["enabled"] is True

    @patch("nekonote.scheduler._jobs_path")
    def test_add_with_variables(self, mock_path, tmp_path):
        mock_path.return_value = tmp_path / "schedules.json"

        scheduler.add("v", cron="0 0 * * *", script="x.py", variables={"key": "val"})
        assert scheduler.list()["v"]["variables"]["key"] == "val"
