"""
Content Library API — /api/v1/content/
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from app.deps import require_sales, UserRecord
from app.services import content_service

router = APIRouter()


class ContentCreate(BaseModel):
    title: str
    type: str = "other"
    body: str = ""
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    language: str = "it"
    source: str = "manual"


class ContentUpdate(BaseModel):
    title: Optional[str] = None
    type: Optional[str] = None
    body: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[list[str]] = None
    language: Optional[str] = None


@router.get("/")
async def list_content(
    type: Optional[str] = None,
    tag: Optional[str] = None,
    q: Optional[str] = None,
    user: UserRecord = Depends(require_sales),
):
    return await content_service.list_content(type, tag, q)


@router.get("/stats")
async def content_stats(user: UserRecord = Depends(require_sales)):
    return await content_service.content_stats()


@router.get("/tags")
async def content_tags(user: UserRecord = Depends(require_sales)):
    return await content_service.list_tags()


@router.get("/{content_id}")
async def get_content(
    content_id: str,
    user: UserRecord = Depends(require_sales),
):
    doc = await content_service.get_content(content_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Contenuto non trovato")
    return doc


@router.post("/")
async def create_content(
    body: ContentCreate,
    user: UserRecord = Depends(require_sales),
):
    if body.type not in content_service.TYPES:
        raise HTTPException(status_code=400, detail="Tipo non valido")
    return await content_service.create_content(body.model_dump(), user.uid)


@router.patch("/{content_id}")
async def update_content(
    content_id: str,
    body: ContentUpdate,
    user: UserRecord = Depends(require_sales),
):
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    if "type" in data and data["type"] not in content_service.TYPES:
        raise HTTPException(status_code=400, detail="Tipo non valido")
    doc = await content_service.update_content(content_id, data)
    if not doc:
        raise HTTPException(status_code=404, detail="Contenuto non trovato")
    return doc


@router.delete("/{content_id}")
async def delete_content(
    content_id: str,
    user: UserRecord = Depends(require_sales),
):
    ok = await content_service.delete_content(content_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Contenuto non trovato")
    return {"ok": True}
