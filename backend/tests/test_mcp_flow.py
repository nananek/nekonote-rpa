"""Tests for MCP flow editing tools."""

import json
from unittest.mock import patch

import pytest

from nekonote.mcp_server import (
    get_current_flow,
    update_flow,
    add_block,
    remove_block,
    update_block_params,
)

SAMPLE_FLOW = {
    "version": "1.0",
    "id": "test-flow",
    "name": "Test Flow",
    "description": "",
    "variables": [],
    "blocks": [
        {"id": "b1", "type": "data.log", "label": "Hello", "params": {"message": "hi"}},
        {"id": "b2", "type": "browser.open", "label": "Open", "params": {}},
    ],
}


@pytest.fixture
def flow_file(tmp_path):
    """Create a temp flow file and patch the shared path."""
    path = str(tmp_path / "current_flow.json")
    with open(path, "w") as f:
        json.dump(SAMPLE_FLOW, f)
    with patch("nekonote.mcp_server._get_shared_flow_path", return_value=path):
        yield path


class TestGetCurrentFlow:
    def test_read_flow(self, flow_file):
        result = get_current_flow()
        data = json.loads(result)
        assert data["name"] == "Test Flow"
        assert len(data["blocks"]) == 2

    def test_no_flow_open(self, tmp_path):
        path = str(tmp_path / "nonexistent.json")
        with patch("nekonote.mcp_server._get_shared_flow_path", return_value=path):
            result = get_current_flow()
            assert "error" in json.loads(result)


class TestUpdateFlow:
    def test_replace_flow(self, flow_file):
        new_flow = {**SAMPLE_FLOW, "name": "Updated", "blocks": []}
        result = update_flow(json.dumps(new_flow))
        assert json.loads(result)["status"] == "ok"

        # Verify
        data = json.loads(get_current_flow())
        assert data["name"] == "Updated"
        assert len(data["blocks"]) == 0

    def test_invalid_json(self, flow_file):
        result = update_flow("not json")
        assert "error" in json.loads(result)

    def test_missing_blocks(self, flow_file):
        result = update_flow('{"name": "no blocks"}')
        assert "error" in json.loads(result)


class TestAddBlock:
    def test_add_to_end(self, flow_file):
        result = add_block("browser.navigate", label="Go", params='{"url": "https://example.com"}')
        data = json.loads(result)
        assert data["status"] == "ok"
        assert data["type"] == "browser.navigate"

        flow = json.loads(get_current_flow())
        assert len(flow["blocks"]) == 3
        assert flow["blocks"][2]["type"] == "browser.navigate"
        assert flow["blocks"][2]["params"]["url"] == "https://example.com"

    def test_add_at_index(self, flow_file):
        add_block("data.log", label="Middle", params='{"message": "mid"}', index=1)
        flow = json.loads(get_current_flow())
        assert flow["blocks"][1]["label"] == "Middle"
        assert len(flow["blocks"]) == 3

    def test_add_to_parent(self, flow_file):
        # First add a control block
        flow = json.loads(get_current_flow())
        flow["blocks"].append({
            "id": "ctrl1", "type": "control.if", "label": "If",
            "params": {"condition": "True"}, "children": [], "elseChildren": [],
        })
        update_flow(json.dumps(flow))

        # Add child to it
        result = add_block("data.log", label="Inside", params='{"message": "x"}', parent_id="ctrl1")
        assert json.loads(result)["status"] == "ok"

        flow = json.loads(get_current_flow())
        ctrl = [b for b in flow["blocks"] if b["id"] == "ctrl1"][0]
        assert len(ctrl["children"]) == 1


class TestRemoveBlock:
    def test_remove(self, flow_file):
        result = remove_block("b1")
        assert json.loads(result)["status"] == "ok"

        flow = json.loads(get_current_flow())
        assert len(flow["blocks"]) == 1
        assert flow["blocks"][0]["id"] == "b2"


class TestUpdateBlockParams:
    def test_update(self, flow_file):
        result = update_block_params("b1", '{"message": "updated"}')
        assert json.loads(result)["status"] == "ok"

        flow = json.loads(get_current_flow())
        assert flow["blocks"][0]["params"]["message"] == "updated"

    def test_merge_params(self, flow_file):
        update_block_params("b1", '{"extra": "value"}')
        flow = json.loads(get_current_flow())
        assert flow["blocks"][0]["params"]["message"] == "hi"  # original preserved
        assert flow["blocks"][0]["params"]["extra"] == "value"  # new added

    def test_block_not_found(self, flow_file):
        result = update_block_params("nonexistent", '{"x": 1}')
        assert "error" in json.loads(result)
