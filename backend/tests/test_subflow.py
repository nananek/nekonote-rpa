"""Tests for subflow execution."""

import pytest

from nekonote.engine.executor import FlowExecutor
from nekonote.models.flow import Flow, FlowNode, FlowEdge, SubFlow, Variable


class TestSubflow:
    @pytest.mark.asyncio
    async def test_subflow_call(self):
        events = []

        async def on_event(e):
            events.append(e)

        flow = Flow(
            version="1.0",
            id="main",
            name="Main",
            variables=[],
            nodes=[
                FlowNode(id="n1", type="data.log", params={"message": "before"}),
                FlowNode(id="n2", type="subflow.call", params={"name": "greet", "inputs": {"who": "World"}}),
                FlowNode(id="n3", type="data.log", params={"message": "after"}),
            ],
            edges=[
                FlowEdge(id="e1", source="n1", target="n2"),
                FlowEdge(id="e2", source="n2", target="n3"),
            ],
            subflows=[
                SubFlow(
                    id="sf1",
                    name="greet",
                    inputs=[Variable(name="who", type="string", default="")],
                    outputs=[],
                    nodes=[
                        FlowNode(id="s1", type="data.log", params={"message": "Hello {{ who }}"}),
                    ],
                    edges=[],
                ),
            ],
        )

        executor = FlowExecutor(flow, on_event=on_event)
        await executor.execute()

        log_msgs = [e.get("message", "") for e in events if e.get("type") == "log"]
        assert any("Entering subflow" in m for m in log_msgs)
        assert any("Exiting subflow" in m for m in log_msgs)
        completed = [e for e in events if e.get("type") == "execution.completed"]
        assert len(completed) == 1

    @pytest.mark.asyncio
    async def test_subflow_not_found(self):
        flow = Flow(
            version="1.0",
            id="main",
            name="Main",
            nodes=[
                FlowNode(id="n1", type="subflow.call", params={"name": "nonexistent"}),
            ],
            edges=[],
            subflows=[],
        )

        events = []
        executor = FlowExecutor(flow, on_event=lambda e: events.append(e))
        await executor.execute()

        failed = [e for e in events if e.get("type") == "execution.failed"]
        assert len(failed) == 1
        assert "not found" in failed[0].get("error", "").lower()
