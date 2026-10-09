"""
Advanced analytics service — MongoDB aggregation pipelines.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional
from app.services.db_service import db


# ── Conversion Funnel ──────────────────────────────────────────
STAGE_ORDER = ["new", "contacted", "qualified", "proposal", "negotiation", "won", "lost"]

async def get_conversion_funnel(since: Optional[datetime] = None) -> list[dict]:
    """Count leads/deals that reached each pipeline stage."""
    match = {"deletedAt": None}
    if since:
        match["createdAt"] = {"$gte": since}

    # Leads funnel by status
    pipeline = [
        {"$match": match},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
    ]
    status_counts = {}
    async for row in db["leads"].aggregate(pipeline):
        status_counts[row["_id"] or "new"] = row["count"]

    # Deals funnel by stage
    deal_pipeline = [
        {"$match": match},
        {"$group": {"_id": "$stage", "count": {"$sum": 1}}},
    ]
    deal_counts = {}
    async for row in db["deals"].aggregate(deal_pipeline):
        deal_counts[row["_id"] or "new"] = row["count"]

    # Merge into unified funnel
    result = []
    for stage in STAGE_ORDER:
        if stage in ("new", "contacted", "qualified"):
            count = status_counts.get(stage, 0)
        else:
            count = deal_counts.get(stage, 0)
        result.append({"stage": stage, "count": count})

    return result


# ── Pipeline Velocity ──────────────────────────────────────────
async def get_pipeline_velocity() -> list[dict]:
    """Average days a deal spends in each stage (from activities log)."""
    pipeline = [
        {"$match": {"type": "stage_change", "deletedAt": None}},
        {"$sort": {"createdAt": 1}},
        {"$group": {
            "_id": {"leadId": "$leadId", "fromStage": "$details.from", "toStage": "$details.to"},
            "changedAt": {"$first": "$createdAt"},
        }},
        {"$group": {
            "_id": "$_id.fromStage",
            "avgDays": {"$avg": {
                "$divide": [
                    {"$subtract": ["$changedAt", "$changedAt"]},  # placeholder
                    86400000,
                ],
            }},
            "count": {"$sum": 1},
        }},
    ]

    # Simpler approach: compute average age of deals per stage
    result = []
    now = datetime.now(timezone.utc)
    for stage in STAGE_ORDER:
        if stage == "lost":
            continue
        stage_pipeline = [
            {"$match": {"stage": stage, "deletedAt": None}},
            {"$project": {
                "daysInStage": {
                    "$divide": [
                        {"$subtract": [now, "$updatedAt"]},
                        86400000,
                    ]
                }
            }},
            {"$group": {
                "_id": None,
                "avgDays": {"$avg": "$daysInStage"},
                "count": {"$sum": 1},
            }},
        ]
        async for row in db["deals"].aggregate(stage_pipeline):
            result.append({
                "stage": stage,
                "avgDays": round(row.get("avgDays", 0), 1),
                "count": row.get("count", 0),
            })
            break
        else:
            result.append({"stage": stage, "avgDays": 0, "count": 0})

    return result


# ── Sales Performance ──────────────────────────────────────────
async def get_sales_performance(since: Optional[datetime] = None) -> list[dict]:
    """Per-user sales metrics: leads assigned, deals closed, revenue."""
    match = {"deletedAt": None}
    if since:
        match["createdAt"] = {"$gte": since}

    # Leads per assigned user
    leads_pipeline = [
        {"$match": {**match, "assignedTo": {"$ne": None}}},
        {"$group": {"_id": "$assignedTo", "leads": {"$sum": 1}}},
    ]
    user_leads = {}
    async for row in db["leads"].aggregate(leads_pipeline):
        user_leads[row["_id"]] = row["leads"]

    # Deals per assigned user
    deals_pipeline = [
        {"$match": {**match, "assignedTo": {"$ne": None}}},
        {"$group": {
            "_id": {"user": "$assignedTo", "stage": "$stage"},
            "count": {"$sum": 1},
            "value": {"$sum": "$value"},
        }},
    ]
    user_deals: dict = {}
    async for row in db["deals"].aggregate(deals_pipeline):
        uid = row["_id"]["user"]
        stage = row["_id"]["stage"]
        if uid not in user_deals:
            user_deals[uid] = {"won": 0, "wonValue": 0, "active": 0, "activeValue": 0, "lost": 0}
        if stage == "won":
            user_deals[uid]["won"] += row["count"]
            user_deals[uid]["wonValue"] += float(row.get("value") or 0)
        elif stage == "lost":
            user_deals[uid]["lost"] += row["count"]
        else:
            user_deals[uid]["active"] += row["count"]
            user_deals[uid]["activeValue"] += float(row.get("value") or 0)

    # Load user display names
    all_uids = set(list(user_leads.keys()) + list(user_deals.keys()))
    users_map = {}
    if all_uids:
        async for u in db["users"].find({"_id": {"$in": list(all_uids)}}):
            users_map[u["_id"]] = u.get("displayName") or u.get("email", u["_id"])

    result = []
    for uid in all_uids:
        ld = user_leads.get(uid, 0)
        dd = user_deals.get(uid, {"won": 0, "wonValue": 0, "active": 0, "activeValue": 0, "lost": 0})
        closed = dd["won"] + dd["lost"]
        result.append({
            "userId": uid,
            "userName": users_map.get(uid, uid),
            "leads": ld,
            "dealsWon": dd["won"],
            "dealsActive": dd["active"],
            "dealsLost": dd["lost"],
            "revenue": dd["wonValue"],
            "pipelineValue": dd["activeValue"],
            "winRate": round(dd["won"] / closed * 100, 1) if closed > 0 else 0,
        })

    result.sort(key=lambda x: x["revenue"], reverse=True)
    return result


# ── Time-Series Trends ──────────────────────────────────────────
async def get_trends(period: str = "week", since: Optional[datetime] = None) -> dict:
    """Leads created and deals won/lost per time bucket."""
    if not since:
        since = datetime.now(timezone.utc) - timedelta(days=90)

    group_format = "%Y-W%V" if period == "week" else "%Y-%m"

    leads_pipeline = [
        {"$match": {"deletedAt": None, "createdAt": {"$gte": since}}},
        {"$group": {
            "_id": {"$dateToString": {"format": group_format, "date": "$createdAt"}},
            "leads": {"$sum": 1},
        }},
        {"$sort": {"_id": 1}},
    ]
    leads_by_period = {}
    async for row in db["leads"].aggregate(leads_pipeline):
        leads_by_period[row["_id"]] = row["leads"]

    deals_pipeline = [
        {"$match": {"deletedAt": None, "createdAt": {"$gte": since}}},
        {"$group": {
            "_id": {
                "period": {"$dateToString": {"format": group_format, "date": "$createdAt"}},
                "stage": "$stage",
            },
            "count": {"$sum": 1},
            "value": {"$sum": "$value"},
        }},
        {"$sort": {"_id.period": 1}},
    ]
    deals_by_period: dict = {}
    async for row in db["deals"].aggregate(deals_pipeline):
        p = row["_id"]["period"]
        stage = row["_id"]["stage"]
        if p not in deals_by_period:
            deals_by_period[p] = {"won": 0, "wonValue": 0, "lost": 0, "newDeals": 0}
        if stage == "won":
            deals_by_period[p]["won"] += row["count"]
            deals_by_period[p]["wonValue"] += float(row.get("value") or 0)
        elif stage == "lost":
            deals_by_period[p]["lost"] += row["count"]
        else:
            deals_by_period[p]["newDeals"] += row["count"]

    # Merge
    all_periods = sorted(set(list(leads_by_period.keys()) + list(deals_by_period.keys())))
    series = []
    for p in all_periods:
        dd = deals_by_period.get(p, {"won": 0, "wonValue": 0, "lost": 0, "newDeals": 0})
        series.append({
            "period": p,
            "leads": leads_by_period.get(p, 0),
            "dealsWon": dd["won"],
            "dealsWonValue": dd["wonValue"],
            "dealsLost": dd["lost"],
            "newDeals": dd["newDeals"],
        })

    return {"period": period, "series": series}


# ── Weighted Forecast ──────────────────────────────────────────
async def get_forecast() -> list[dict]:
    """Weighted pipeline forecast by stage (value * probability)."""
    pipeline = [
        {"$match": {"deletedAt": None, "stage": {"$nin": ["won", "lost"]}}},
        {"$group": {
            "_id": "$stage",
            "totalValue": {"$sum": "$value"},
            "weightedValue": {"$sum": {"$multiply": ["$value", {"$divide": ["$probability", 100]}]}},
            "count": {"$sum": 1},
            "avgProbability": {"$avg": "$probability"},
        }},
        {"$sort": {"totalValue": -1}},
    ]
    result = []
    async for row in db["deals"].aggregate(pipeline):
        result.append({
            "stage": row["_id"],
            "count": row["count"],
            "totalValue": round(float(row["totalValue"]), 2),
            "weightedValue": round(float(row["weightedValue"]), 2),
            "avgProbability": round(float(row["avgProbability"]), 1),
        })

    return result


# ── Lead Cohorts ───────────────────────────────────────────────
async def get_cohorts(months_back: int = 6) -> list[dict]:
    """Monthly cohorts: how many leads created each month, and how many moved to each status."""
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=months_back * 30)

    # Leads created per month
    creation_pipeline = [
        {"$match": {"deletedAt": None, "createdAt": {"$gte": since}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m", "date": "$createdAt"}},
            "total": {"$sum": 1}},
        },
        {"$sort": {"_id": 1}},
    ]
    cohorts = {}
    async for row in db["leads"].aggregate(creation_pipeline):
        month = row["_id"]
        cohorts[month] = {"month": month, "total": row["total"], "contacted": 0, "qualified": 0, "converted": 0}

    # How many of those leads have been contacted
    contacted_pipeline = [
        {"$match": {"deletedAt": None, "createdAt": {"$gte": since}, "status": {"$in": ["contacted", "qualified", "proposal", "negotiation", "won"]}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m", "date": "$createdAt"}},
            "count": {"$sum": 1}},
        },
    ]
    async for row in db["leads"].aggregate(contacted_pipeline):
        if row["_id"] in cohorts:
            cohorts[row["_id"]]["contacted"] = row["count"]

    # How many are qualified
    qualified_pipeline = [
        {"$match": {"deletedAt": None, "createdAt": {"$gte": since}, "status": {"$in": ["qualified", "proposal", "negotiation", "won"]}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m", "date": "$createdAt"}},
            "count": {"$sum": 1}},
        },
    ]
    async for row in db["leads"].aggregate(qualified_pipeline):
        if row["_id"] in cohorts:
            cohorts[row["_id"]]["qualified"] = row["count"]

    # How many converted (have a won deal)
    won_lead_ids = []
    async for deal in db["deals"].find({"stage": "won", "deletedAt": None}, {"leadId": 1}):
        won_lead_ids.append(deal["leadId"])

    if won_lead_ids:
        converted_pipeline = [
            {"$match": {"deletedAt": None, "_id": {"$in": won_lead_ids}, "createdAt": {"$gte": since}}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m", "date": "$createdAt"}},
                "count": {"$sum": 1}},
            },
        ]
        async for row in db["leads"].aggregate(converted_pipeline):
            if row["_id"] in cohorts:
                cohorts[row["_id"]]["converted"] = row["count"]

    result = list(cohorts.values())
    # Add rates
    for c in result:
        total = c["total"]
        c["contactRate"] = round(c["contacted"] / total * 100, 1) if total > 0 else 0
        c["qualifyRate"] = round(c["qualified"] / total * 100, 1) if total > 0 else 0
        c["convertRate"] = round(c["converted"] / total * 100, 1) if total > 0 else 0

    return result


# ── KPI Summary (for report snapshots) ─────────────────────────
async def get_kpi_summary(since: Optional[datetime] = None) -> dict:
    """Full KPI snapshot for report generation."""
    match = {"deletedAt": None}
    if since:
        match["createdAt"] = {"$gte": since}

    total_leads = await db["leads"].count_documents({"deletedAt": None})
    new_leads = await db["leads"].count_documents({**match})

    deals_match = {"deletedAt": None}
    if since:
        deals_match["createdAt"] = {"$gte": since}

    won_deals = await db["deals"].count_documents({**deals_match, "stage": "won"})
    lost_deals = await db["deals"].count_documents({**deals_match, "stage": "lost"})
    active_deals = await db["deals"].count_documents({**deals_match, "stage": {"$nin": ["won", "lost"]}})

    # Pipeline value
    pv_pipeline = [
        {"$match": {**deals_match, "stage": {"$nin": ["won", "lost"]}}},
        {"$group": {"_id": None, "total": {"$sum": "$value"}}},
    ]
    pipeline_value = 0.0
    async for row in db["deals"].aggregate(pv_pipeline):
        pipeline_value = float(row["total"])

    # Revenue (won deals)
    rev_pipeline = [
        {"$match": {**deals_match, "stage": "won"}},
        {"$group": {"_id": None, "total": {"$sum": "$value"}}},
    ]
    revenue = 0.0
    async for row in db["deals"].aggregate(rev_pipeline):
        revenue = float(row["total"])

    closed = won_deals + lost_deals
    conversion_rate = round(won_deals / closed * 100, 1) if closed > 0 else 0.0

    # Top sources
    source_pipeline = [
        {"$match": {"deletedAt": None}},
        {"$group": {"_id": "$source", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5},
    ]
    top_sources = []
    async for row in db["leads"].aggregate(source_pipeline):
        top_sources.append({"source": row["_id"] or "direct", "count": row["count"]})

    return {
        "totalLeads": total_leads,
        "newLeads": new_leads,
        "wonDeals": won_deals,
        "lostDeals": lost_deals,
        "activeDeals": active_deals,
        "pipelineValue": pipeline_value,
        "revenue": revenue,
        "conversionRate": conversion_rate,
        "topSources": top_sources,
    }