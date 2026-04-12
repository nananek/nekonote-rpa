from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from nekonote.engine.nodes.registry import get_all_types
from nekonote.models.flow import Flow

router = APIRouter(prefix="/api")


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"


class ValidateResponse(BaseModel):
    valid: bool
    errors: list[str] = []


@router.get("/health")
async def health() -> HealthResponse:
    return HealthResponse()


@router.get("/nodes/types")
async def node_types() -> list[str]:
    return get_all_types()


@router.post("/flow/validate")
async def validate_flow(flow: Flow) -> ValidateResponse:
    errors: list[str] = []

    if not flow.nodes:
        errors.append("Flow has no nodes")

    node_ids = {n.id for n in flow.nodes}
    for edge in flow.edges:
        if edge.source not in node_ids:
            errors.append(f"Edge {edge.id}: source '{edge.source}' not found")
        if edge.target not in node_ids:
            errors.append(f"Edge {edge.id}: target '{edge.target}' not found")

    return ValidateResponse(valid=len(errors) == 0, errors=errors)
