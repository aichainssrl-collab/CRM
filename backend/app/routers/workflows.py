"""
Workflows API — /api/v1/workflows/
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Optional
from app.deps import require_sales, UserRecord
from app.services import workflow_service

router = APIRouter()


class Condition(BaseModel):
    field: str
    op: str = "eq"
    value: Any = None


class Action(BaseModel):
    type: str
    title: Optional[str] = None
    description: Optional[str] = None
    dueDate: Optional[str] = None
    priority: str = "medium"
    assignedTo: Optional[str] = None
    tag: Optional[str] = None
    status: Optional[str] = None
    userId: Optional[str] = None
    body: Optional[str] = None
    to: Optional[str] = None
    subject: Optional[str] = None


class WorkflowCreate(BaseModel):
    name: str
    description: str = ""
    trigger: str = "manual"
    conditions: list[Condition] = Field(default_factory=list)
    actions: list[Action] = Field(default_factory=list)
    isActive: bool = False


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    trigger: Optional[str] = None
    conditions: Optional[list[Condition]] = None
    actions: Optional[list[Action]] = None
    isActive: Optional[bool] = None


class TriggerRequest(BaseModel):
    trigger: str
    entity: dict = Field(default_factory=dict)


@router.get("/")
async def list_workflows(
    only_active: bool = False,
    user: UserRecord = Depends(require_sales),
):
    return await workflow_service.list_workflows(only_active)


@router.get("/stats")
async def workflow_stats(user: UserRecord = Depends(require_sales)):
    return await workflow_service.workflow_stats()


@router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    user: UserRecord = Depends(require_sales),
):
    doc = await workflow_service.get_workflow(workflow_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Workflow non trovato")
    return doc


@router.post("/")
async def create_workflow(
    body: WorkflowCreate,
    user: UserRecord = Depends(require_sales),
):
    if body.trigger not in workflow_service.TRIGGERS:
        raise HTTPException(status_code=400, detail="Trigger non valido")
    for action in body.actions:
        if action.type not in workflow_service.ACTION_TYPES:
            raise HTTPException(status_code=400, detail=f"Azione non valida: {action.type}")
    return await workflow_service.create_workflow(body.model_dump(), user.uid)


@router.patch("/{workflow_id}")
async def update_workflow(
    workflow_id: str,
    body: WorkflowUpdate,
    user: UserRecord = Depends(require_sales),
):
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    if "trigger" in data and data["trigger"] not in workflow_service.TRIGGERS:
        raise HTTPException(status_code=400, detail="Trigger non valido")
    doc = await workflow_service.update_workflow(workflow_id, data)
    if not doc:
        raise HTTPException(status_code=404, detail="Workflow non trovato")
    return doc


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    user: UserRecord = Depends(require_sales),
):
    ok = await workflow_service.delete_workflow(workflow_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Workflow non trovato")
    return {"ok": True}


@router.post("/{workflow_id}/toggle")
async def toggle_workflow(
    workflow_id: str,
    user: UserRecord = Depends(require_sales),
):
    doc = await workflow_service.toggle_workflow(workflow_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Workflow non trovato")
    return doc


@router.post("/trigger")
async def fire_trigger(
    body: TriggerRequest,
    user: UserRecord = Depends(require_sales),
):
    """Fire a trigger with an entity payload — runs matching active workflows."""
    results = await workflow_service.run_workflows(body.trigger, body.entity, user.uid)
    return {"fired": len(results), "results": results}
