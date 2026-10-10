"""
Product Catalog & Segmentation API — /api/v1/products/ and /api/v1/segments/
"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional
from app.deps import require_sales, UserRecord
from app.services import product_service, segmentation_service

router = APIRouter()
seg_router = APIRouter()


# ── Product Schemas ────────────────────────────────────────────
class ProductCreate(BaseModel):
    name: str
    description: str = ""
    sku: str = ""
    category: str = "software"
    price: float = 0
    currency: str = "EUR"
    billingModel: str = "one-time"
    isActive: bool = True


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    billingModel: Optional[str] = None
    isActive: Optional[bool] = None


# ── Segment Schemas ────────────────────────────────────────────
class SegmentCreate(BaseModel):
    name: str
    description: str = ""
    rules: dict = {}
    entityType: str = "leads"
    isGlobal: bool = False


# ── Product Endpoints ──────────────────────────────────────────
@router.get("")
@router.get("/")
async def list_products(
    active_only: bool = Query(True),
    user: UserRecord = Depends(require_sales),
):
    return await product_service.list_products(active_only)


@router.get("/{product_id}")
async def get_product(
    product_id: str,
    user: UserRecord = Depends(require_sales),
):
    return await product_service.get_product(product_id)


@router.post("")
@router.post("/")
async def create_product(
    body: ProductCreate,
    user: UserRecord = Depends(require_sales),
):
    return await product_service.create_product(body.model_dump(), user.uid)


@router.patch("/{product_id}")
async def update_product(
    product_id: str,
    body: ProductUpdate,
    user: UserRecord = Depends(require_sales),
):
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    return await product_service.update_product(product_id, data)


@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    user: UserRecord = Depends(require_sales),
):
    ok = await product_service.delete_product(product_id)
    return {"ok": ok}


# ── Segment Endpoints ─────────────────────────────────────────
@seg_router.get("")
@seg_router.get("/")
async def list_segments(user: UserRecord = Depends(require_sales)):
    return await segmentation_service.list_segments(user.uid)


@seg_router.post("")
@seg_router.post("/")
async def create_segment(
    body: SegmentCreate,
    user: UserRecord = Depends(require_sales),
):
    return await segmentation_service.create_segment(user.uid, body.model_dump())


@seg_router.get("/{segment_id}/results")
async def segment_results(
    segment_id: str,
    limit: int = Query(100, ge=1, le=500),
    user: UserRecord = Depends(require_sales),
):
    return await segmentation_service.get_segment_results(segment_id, limit)


@seg_router.delete("/{segment_id}")
async def delete_segment(
    segment_id: str,
    user: UserRecord = Depends(require_sales),
):
    ok = await segmentation_service.delete_segment(segment_id)
    return {"ok": ok}


# ── Analytics Endpoints ───────────────────────────────────────
@seg_router.get("/analytics/tags")
async def tag_analytics(user: UserRecord = Depends(require_sales)):
    return await segmentation_service.get_tag_analytics()


@seg_router.get("/analytics/industries")
async def industry_segments(user: UserRecord = Depends(require_sales)):
    return await segmentation_service.get_industry_segments()


@seg_router.get("/analytics/sources")
async def source_performance(user: UserRecord = Depends(require_sales)):
    return await segmentation_service.get_source_performance()