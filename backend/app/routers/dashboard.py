from fastapi import APIRouter, Depends, Query
from datetime import datetime, timezone, timedelta
from app.deps import require_sales, UserRecord
from app.services.db_service import db

router = APIRouter()

_TIME_RANGE_DAYS = {"7d": 7, "30d": 30, "90d": 90}


@router.get("/metrics")
async def get_dashboard_metrics(
    time_range: str = Query("30d", description="7d | 30d | 90d"),
    user: UserRecord = Depends(require_sales),
):
    days = _TIME_RANGE_DAYS.get(time_range, 30)
    since = datetime.now(timezone.utc) - timedelta(days=days)

    total_leads = await db["leads"].count_documents({"deletedAt": None})
    new_leads = await db["leads"].count_documents({"deletedAt": None, "createdAt": {"$gte": since}})

    pipeline = [
        {"$match": {"deletedAt": None}},
        {"$group": {
            "_id": "$stage",
            "count": {"$sum": 1},
            "value": {"$sum": "$value"},
        }},
    ]
    won_count = lost_count = active_deals = 0
    pipeline_value = 0.0
    async for row in db["deals"].aggregate(pipeline):
        stage = row["_id"] or ""
        if stage == "won":
            won_count += row["count"]
        elif stage == "lost":
            lost_count += row["count"]
        else:
            active_deals += row["count"]
            pipeline_value += float(row.get("value") or 0)

    closed = won_count + lost_count
    conversion_rate = round(won_count / closed * 100, 2) if closed > 0 else 0.0

    return {
        "totalLeads": total_leads,
        "newLeads": new_leads,
        "activeDeals": active_deals,
        "pipelineValue": pipeline_value,
        "conversionRate": conversion_rate,
    }
