"""
Email Templates API — /api/v1/email-templates/
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.deps import require_sales, UserRecord
from app.services import email_template_service as svc

router = APIRouter()


class TemplateCreate(BaseModel):
    name: str
    key: str = ""
    subject: str = ""
    bodyHtml: str = ""
    category: str = "other"


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    key: Optional[str] = None
    subject: Optional[str] = None
    bodyHtml: Optional[str] = None
    category: Optional[str] = None


@router.get("/")
async def list_templates(
    category: Optional[str] = None,
    user: UserRecord = Depends(require_sales),
):
    return await svc.list_templates(category)


@router.get("/{template_id}")
async def get_template(
    template_id: str,
    user: UserRecord = Depends(require_sales),
):
    doc = await svc.get_template(template_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Template non trovato")
    return doc


@router.post("/")
async def create_template(
    body: TemplateCreate,
    user: UserRecord = Depends(require_sales),
):
    return await svc.create_template(body.model_dump(), user.uid)


@router.patch("/{template_id}")
async def update_template(
    template_id: str,
    body: TemplateUpdate,
    user: UserRecord = Depends(require_sales),
):
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    doc = await svc.update_template(template_id, data)
    if not doc:
        raise HTTPException(status_code=404, detail="Template non trovato")
    return doc


@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    user: UserRecord = Depends(require_sales),
):
    ok = await svc.delete_template(template_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Template non trovato")
    return {"ok": True}
