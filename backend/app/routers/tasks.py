from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from app.deps import require_sales, UserRecord
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.task_service import (
    create_task, list_tasks, get_task, update_task,
    complete_task, delete_task,
)
from app.services.db_service import get_document

router = APIRouter()


@router.get("/{lead_id}/tasks")
async def get_tasks(
    lead_id: str,
    status: Optional[str] = Query(None),
    user: UserRecord = Depends(require_sales),
):
    lead = await get_document("leads", lead_id)
    if not lead:
        raise HTTPException(404, "Lead non trovato")
    return await list_tasks(lead_id, status=status)


@router.post("/{lead_id}/tasks", status_code=201)
async def create_lead_task(
    lead_id: str,
    data: TaskCreate,
    user: UserRecord = Depends(require_sales),
):
    lead = await get_document("leads", lead_id)
    if not lead:
        raise HTTPException(404, "Lead non trovato")
    return await create_task(lead_id, data, created_by=user.uid)


@router.patch("/{lead_id}/tasks/{task_id}")
async def update_lead_task(
    lead_id: str,
    task_id: str,
    data: TaskUpdate,
    user: UserRecord = Depends(require_sales),
):
    task = await get_task(lead_id, task_id)
    if not task:
        raise HTTPException(404, "Task non trovato")
    return await update_task(lead_id, task_id, data, updated_by=user.uid)


@router.post("/{lead_id}/tasks/{task_id}/complete")
async def complete_lead_task(
    lead_id: str,
    task_id: str,
    user: UserRecord = Depends(require_sales),
):
    task = await get_task(lead_id, task_id)
    if not task:
        raise HTTPException(404, "Task non trovato")
    return await complete_task(lead_id, task_id, completed_by=user.uid)


@router.delete("/{lead_id}/tasks/{task_id}", status_code=204)
async def delete_lead_task(
    lead_id: str,
    task_id: str,
    user: UserRecord = Depends(require_sales),
):
    task = await get_task(lead_id, task_id)
    if not task:
        raise HTTPException(404, "Task non trovato")
    await delete_task(lead_id, task_id)
