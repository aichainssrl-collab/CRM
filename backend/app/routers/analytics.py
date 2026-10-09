"""
Advanced analytics endpoints — /api/v1/analytics/
"""
from fastapi import APIRouter, Depends, Query
from datetime import datetime, timezone, timedelta
from app.deps import require_sales, UserRecord
from app.services import analytics_service

router = APIRouter()

_TIME_RANGE_DAYS = {"7d": 7, "30d": 30, "90d": 90, "all": None}


def _since_from_range(time_range: str) -> datetime | None:
    days = _TIME_RANGE_DAYS.get(time_range, 90)
    if days is None:
        return None
    return datetime.now(timezone.utc) - timedelta(days=days)


@router.get("/funnel")
async def conversion_funnel(
    time_range: str = Query("90d"),
    user: UserRecord = Depends(require_sales),
):
    since = _since_from_range(time_range)
    data = await analytics_service.get_conversion_funnel(since)
    return {"funnel": data, "timeRange": time_range}


@router.get("/velocity")
async def pipeline_velocity(
    user: UserRecord = Depends(require_sales),
):
    data = await analytics_service.get_pipeline_velocity()
    return {"velocity": data}


@router.get("/performance")
async def sales_performance(
    time_range: str = Query("90d"),
    user: UserRecord = Depends(require_sales),
):
    since = _since_from_range(time_range)
    data = await analytics_service.get_sales_performance(since)
    return {"performance": data, "timeRange": time_range}


@router.get("/trends")
async def trends(
    period: str = Query("week", pattern="^(week|month)$"),
    time_range: str = Query("90d"),
    user: UserRecord = Depends(require_sales),
):
    since = _since_from_range(time_range)
    data = await analytics_service.get_trends(period, since)
    return data


@router.get("/forecast")
async def pipeline_forecast(
    user: UserRecord = Depends(require_sales),
):
    data = await analytics_service.get_forecast()
    total_weighted = sum(d["weightedValue"] for d in data)
    total_pipeline = sum(d["totalValue"] for d in data)
    return {
        "forecast": data,
        "totalWeighted": round(total_weighted, 2),
        "totalPipeline": round(total_pipeline, 2),
    }


@router.get("/cohorts")
async def lead_cohorts(
    months: int = Query(6, ge=1, le=24),
    user: UserRecord = Depends(require_sales),
):
    data = await analytics_service.get_cohorts(months)
    return {"cohorts": data}