"""Tests for nekonote.history."""

from unittest.mock import patch

from nekonote import history


class TestHistory:
    @patch("nekonote.history._db_path")
    def test_record_and_list(self, mock_path, tmp_path):
        mock_path.return_value = str(tmp_path / "history.db")

        history.record_event("run1", {"type": "execution.started", "flow_name": "Test"})
        history.record_event("run1", {"type": "log", "message": "hello", "level": "info"})
        history.record_event("run1", {"type": "execution.completed", "status": "success", "duration_ms": 500})

        runs = history.list_runs()
        assert len(runs) == 1
        assert runs[0]["id"] == "run1"
        assert runs[0]["status"] == "success"

    @patch("nekonote.history._db_path")
    def test_get_run_logs(self, mock_path, tmp_path):
        mock_path.return_value = str(tmp_path / "history.db")

        history.record_event("run2", {"type": "execution.started"})
        history.record_event("run2", {"type": "node.enter", "node_id": "n1"})
        history.record_event("run2", {"type": "node.exit", "node_id": "n1"})

        logs = history.get_run_logs("run2")
        assert len(logs) == 3
        assert logs[1]["type"] == "node.enter"

    @patch("nekonote.history._db_path")
    def test_clear(self, mock_path, tmp_path):
        mock_path.return_value = str(tmp_path / "history.db")

        history.record_event("run3", {"type": "execution.started"})
        history.clear()
        assert history.list_runs() == []

    @patch("nekonote.history._db_path")
    def test_failed_run(self, mock_path, tmp_path):
        mock_path.return_value = str(tmp_path / "history.db")

        history.record_event("run4", {"type": "execution.started", "flow_name": "Fail"})
        history.record_event("run4", {"type": "execution.failed", "error": "boom"})

        runs = history.list_runs()
        assert runs[0]["status"] == "failed"
        assert runs[0]["error"] == "boom"
