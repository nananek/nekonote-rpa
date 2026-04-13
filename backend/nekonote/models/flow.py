from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Position(BaseModel):
    x: float = 0
    y: float = 0


class Variable(BaseModel):
    name: str
    type: str = "string"
    default: Any = None


class FlowNode(BaseModel):
    id: str
    type: str
    label: str = ""
    position: Position = Field(default_factory=Position)
    params: dict[str, Any] = Field(default_factory=dict)


class FlowEdge(BaseModel):
    id: str
    source: str
    target: str
    sourceHandle: str = "out"
    targetHandle: str = "in"


class SubFlow(BaseModel):
    """A reusable sub-flow (function) with inputs and outputs."""
    id: str = ""
    name: str = ""
    inputs: list[Variable] = Field(default_factory=list)
    outputs: list[Variable] = Field(default_factory=list)
    nodes: list[FlowNode] = Field(default_factory=list)
    edges: list[FlowEdge] = Field(default_factory=list)


class Flow(BaseModel):
    version: str = "1.0"
    id: str = ""
    name: str = ""
    description: str = ""
    variables: list[Variable] = Field(default_factory=list)
    nodes: list[FlowNode] = Field(default_factory=list)
    edges: list[FlowEdge] = Field(default_factory=list)
    subflows: list[SubFlow] = Field(default_factory=list)
