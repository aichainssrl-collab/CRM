"""
Apollo.io prospect search & enrichment API — /api/v1/apollo/
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.deps import require_sales, UserRecord
from app.services import apollo_service

router = APIRouter()


class SearchFilters(BaseModel):
    q: Optional[str] = None
    title: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    seniority: Optional[str] = None


class SearchBody(BaseModel):
    filters: SearchFilters = Field(default_factory=SearchFilters)
    page: int = 1
    perPage: int = 25


class ImportBody(BaseModel):
    prospects: list[dict]


class EnrichBody(BaseModel):
    email: Optional[str] = None


@router.get("/usage")
async def get_usage(user: UserRecord = Depends(require_sales)):
    return await apollo_service.usage()


@router.post("/search")
async def search_prospects(
    body: SearchBody,
    user: UserRecord = Depends(require_sales),
):
    return await apollo_service.people_search(
        body.filters.model_dump(exclude_none=True),
        page=body.page,
        per_page=body.perPage,
    )


@router.post("/import")
async def import_prospects(
    body: ImportBody,
    user: UserRecord = Depends(require_sales),
):
    if not body.prospects:
        raise HTTPException(status_code=400, detail="Nessun prospect selezionato")
    if len(body.prospects) > 100:
        raise HTTPException(status_code=400, detail="Max 100 prospect per import")
    return await apollo_service.import_prospects(body.prospects, user.uid)


@router.post("/match")
async def match_person(
    body: EnrichBody,
    user: UserRecord = Depends(require_sales),
):
    if not body.email:
        raise HTTPException(status_code=400, detail="Email richiesta")
    person = await apollo_service.people_match(body.email)
    return person or {}


@router.post("/enrich/{lead_id}")
async def enrich_lead(
    lead_id: str,
    user: UserRecord = Depends(require_sales),
):
    lead = await apollo_service.enrich_lead(lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead non trovato")
    return lead
