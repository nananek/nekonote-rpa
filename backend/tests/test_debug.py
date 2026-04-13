"""Tests for debug features (breakpoints, step, variable extensions)."""

import asyncio

import pytest

from nekonote.engine.context import ExecutionContext
from nekonote.engine.executor import FlowExecutor
from nekonote.models.flow import Flow, FlowNode, FlowEdge


class TestContextExtensions:
    def test_secret_variable(self):
        ctx = ExecutionContext()
        ctx.set("password", "secret123", secret=True)
        assert ctx.get("password") == "secret123"
        assert ctx.is_secret("password") is True
        visible = ctx.get_visible_variables()
        assert visible["password"] == "****"

    def test_type_hint(self):
        ctx = ExecutionContext()
        ctx.set("count", 42, type_hint="int")
        assert ctx.get_type("count") == "int"

    def test_auto_type_detection(self):
        ctx = ExecutionContext()
        ctx.set("name", "hello")
        ctx.set("num", 42)
        ctx.set("items", [1, 2, 3])
        assert ctx.get_type("name") == "str"
        assert ctx.get_type("num") == "int"
        assert ctx.get_type("items") == "list"

    def test_hidden_variables(self):
        ctx = ExecutionContext()
        ctx.set("visible", "yes")
        ctx.set("_internal", "hidden")
        visible = ctx.get_visible_variables()
        assert "visible" in visible
        assert "_internal" not in visible


class TestDebugExecution:
    def _make_flow(self):
        return Flow(
            version="1.0",
            id="test",
            name="Debug Test",
            description="",
            variables=[],
            nodes=[
                FlowNode(id="n1", type="data.log", params={"message": "step1"}),
                FlowNode(id="n2", type="data.log", params={"message": "step2"}),
                FlowNode(id="n3", type="data.log", params={"message": "step3"}),
            ],
            edges=[
                FlowEdge(id="e1", source="n1", target="n2"),
                FlowEdge(id="e2", source="n2", target="n3"),
            ],
        )

    @pytest.mark.asyncio
    async def test_breakpoint_pauses(self):
        flow = self._make_flow()
        events = []

        async def on_event(e):
            events.append(e)

        executor = FlowExecutor(flow, on_event=on_event)
        executor.set_breakpoint("n2")

        # Run in background
        task = asyncio.create_task(executor.execute())

        # Wait for pause
        await asyncio.sleep(0.1)
        assert executor._paused is True
        paused_events = [e for e in events if e.get("type") == "debug.paused"]
        assert len(paused_events) == 1
        assert paused_events[0]["node_id"] == "n2"

        # Resume
        executor.resume()
        await task

        completed = [e for e in events if e.get("type") == "execution.completed"]
        assert len(completed) == 1

    @pytest.mark.asyncio
    async def test_step_mode(self):
        flow = self._make_flow()
        events = []

        async def on_event(e):
            events.append(e)

        executor = FlowExecutor(flow, on_event=on_event)
        executor._step_mode = True

        task = asyncio.create_task(executor.execute())
        await asyncio.sleep(0.1)

        # Should be paused at n1
        assert executor._paused is True

        # Step to n2
        executor.step()
        await asyncio.sleep(0.1)
        assert executor._paused is True

        # Step to n3
        executor.step()
        await asyncio.sleep(0.1)
        assert executor._paused is True

        # Resume to finish
        executor.resume()
        await task

    @pytest.mark.asyncio
    async def test_cancel_while_paused(self):
        flow = self._make_flow()
        executor = FlowExecutor(flow)
        executor.set_breakpoint("n1")

        task = asyncio.create_task(executor.execute())
        await asyncio.sleep(0.1)
        assert executor._paused is True

        executor.cancel()
        await task
        # Should have completed without error (cancelled)
