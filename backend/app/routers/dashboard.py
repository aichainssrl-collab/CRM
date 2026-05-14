from fastapi import APIRouter, Depends, Query
from datetime import datetime, timezone, timedelta
from google.cloud.firestore_v1 import FieldFilter
from app.deps import require_sales, UserRecord
from app.firebase_admin import db

router = APIRouter()

_TIME_RANGE_DAYS = {"7d": 7, "30d": 30, "90d": 90}


@router.get("/metrics")
async def get_dashboard_metrics(
    time_range: str = Query("30d", description="7d | 30d | 90d"),
    user: UserRecord = Depends(require_sales),
):
    days = _TIME_RANGE_DAYS.get(time_range, 30)
    since = datetime.now(timezone.utc) - timedelta(days=days)

    total_leads = 0
    new_leads = 0
    async for snap in (
        db.collection("leads")
        .where(filter=FieldFilter("deletedAt", "==", None))
        .stream()
    ):
        total_leads += 1
        doc = snap.to_dict()
        created_at = doc.get("createdAt")
        if created_at and created_at >= since:
            new_leads += 1

    active_deals = 0
    pipeline_value = 0.0
    won_count = 0
    lost_count = 0
    async for snap in (
        db.collection("deals")
        .where(filter=FieldFilter("deletedAt", "==", None))
        .stream()
    ):
        doc = snap.to_dict()
        stage = doc.get("stage", "")
        if stage == "won":
            won_count += 1
        elif stage == "lost":
            lost_count += 1
        else:
            active_deals += 1
            pipeline_value += float(doc.get("value") or 0)

    closed = won_count + lost_count
    conversion_rate = round(won_count / closed * 100, 2) if closed > 0 else 0.0

    return {
        "totalLeads": total_leads,
        "newLeads": new_leads,
        "activeDeals": active_deals,
        "pipelineValue": pipeline_value,
        "conversionRate": conversion_rate,
    }
