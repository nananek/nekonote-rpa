"""Tests for nekonote.recorder (unit tests for block conversion)."""

from nekonote.recorder import _events_to_blocks


class TestEventsToBlocks:
    def test_click_event(self):
        events = [{"time": 0, "type": "click", "x": 100, "y": 200, "button": "left"}]
        blocks = _events_to_blocks(events)
        assert len(blocks) == 1
        assert blocks[0]["type"] == "desktop.click"
        assert blocks[0]["params"]["x"] == 100

    def test_type_event(self):
        events = [{"time": 0, "type": "type", "text": "hello"}]
        blocks = _events_to_blocks(events)
        assert len(blocks) == 1
        assert blocks[0]["type"] == "desktop.type"
        assert blocks[0]["params"]["text"] == "hello"

    def test_hotkey_event(self):
        events = [{"time": 0, "type": "hotkey", "key": "enter"}]
        blocks = _events_to_blocks(events)
        assert len(blocks) == 1
        assert blocks[0]["type"] == "desktop.hotkey"

    def test_wait_inserted_for_gap(self):
        events = [
            {"time": 0, "type": "click", "x": 10, "y": 20, "button": "left"},
            {"time": 2.0, "type": "click", "x": 30, "y": 40, "button": "left"},
        ]
        blocks = _events_to_blocks(events)
        assert len(blocks) == 3  # click, wait, click
        assert blocks[1]["type"] == "control.wait"
        assert blocks[1]["params"]["seconds"] == 2.0

    def test_no_wait_for_short_gap(self):
        events = [
            {"time": 0, "type": "type", "text": "a"},
            {"time": 0.2, "type": "type", "text": "b"},
        ]
        blocks = _events_to_blocks(events)
        assert len(blocks) == 2  # no wait block

    def test_mixed_events(self):
        events = [
            {"time": 0, "type": "click", "x": 100, "y": 200, "button": "left"},
            {"time": 0.1, "type": "type", "text": "hello"},
            {"time": 0.3, "type": "hotkey", "key": "enter"},
        ]
        blocks = _events_to_blocks(events)
        assert blocks[0]["type"] == "desktop.click"
        assert blocks[1]["type"] == "desktop.type"
        assert blocks[2]["type"] == "desktop.hotkey"

    def test_block_ids_unique(self):
        events = [
            {"time": 0, "type": "click", "x": 1, "y": 2, "button": "left"},
            {"time": 0, "type": "click", "x": 3, "y": 4, "button": "left"},
        ]
        blocks = _events_to_blocks(events)
        ids = [b["id"] for b in blocks]
        assert len(set(ids)) == len(ids)
