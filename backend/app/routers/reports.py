"""
Report generation & management — /api/v1/reports/
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone, timedelta
from app.deps import require_sales, require_admin, UserRecord
from app.services.db_service import db, new_id, utcnow, _to_dict
from app.services import analytics_service
from app.services.email_service import send_email
from app.config import settings

router = APIRouter()


class ReportGenerate(BaseModel):
    title: str = "Report CRM"
    timeRange: str = "30d"
    includeFunnel: bool = True
    includeVelocity: bool = True
    includePerformance: bool = True
    includeForecast: bool = True


class ReportSend(BaseModel):
    to: str
    message: Optional[str] = None


# ── Generate ───────────────────────────────────────────────────
@router.post("/generate")
async def generate_report(
    body: ReportGenerate,
    user: UserRecord = Depends(require_sales),
):
    """Generate a report snapshot and store it in MongoDB."""
    days_map = {"7d": 7, "30d": 30, "90d": 90}
    days = days_map.get(body.timeRange, 30)
    since = datetime.now(timezone.utc) - timedelta(days=days)

    report_data = {}

    # KPI summary
    report_data["kpis"] = await analytics_service.get_kpi_summary(since)

    if body.includeFunnel:
        report_data["funnel"] = await analytics_service.get_conversion_funnel(since)

    if body.includeVelocity:
        report_data["velocity"] = await analytics_service.get_pipeline_velocity()

    if body.includePerformance:
        report_data["performance"] = await analytics_service.get_sales_performance(since)

    if body.includeForecast:
        forecast = await analytics_service.get_forecast()
        report_data["forecast"] = forecast
        report_data["forecastTotal"] = {
            "weighted": round(sum(d["weightedValue"] for d in forecast), 2),
            "pipeline": round(sum(d["totalValue"] for d in forecast), 2),
        }

    now = utcnow()
    doc = {
        "_id": new_id(),
        "title": body.title,
        "timeRange": body.timeRange,
        "generatedBy": user.uid,
        "generatedByName": user.displayName or user.email,
        "data": report_data,
        "createdAt": now,
        "updatedAt": now,
        "deletedAt": None,
    }
    await db["reports"].insert_one(doc)

    return _to_dict(doc)


# ── List ───────────────────────────────────────────────────────
@router.get("")
@router.get("/")
async def list_reports(
    limit: int = Query(20, ge=1, le=100),
    user: UserRecord = Depends(require_sales),
):
    cursor = (
        db["reports"]
        .find({"deletedAt": None})
        .sort("createdAt", -1)
        .limit(limit)
    )
    docs = await cursor.to_list(length=limit)
    # Return summary only (not full data payload)
    results = []
    for d in docs:
        d = dict(d)
        d["id"] = d.pop("_id")
        results.append({
            "id": d["id"],
            "title": d.get("title"),
            "timeRange": d.get("timeRange"),
            "generatedBy": d.get("generatedBy"),
            "generatedByName": d.get("generatedByName"),
            "createdAt": d.get("createdAt"),
        })
    return results


# ── Get single ─────────────────────────────────────────────────
@router.get("/{report_id}")
async def get_report(
    report_id: str,
    user: UserRecord = Depends(require_sales),
):
    doc = await db["reports"].find_one({"_id": report_id, "deletedAt": None})
    if not doc:
        raise HTTPException(status_code=404, detail="Report non trovato")
    return _to_dict(doc)


# ── Delete ─────────────────────────────────────────────────────
@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    user: UserRecord = Depends(require_admin),
):
    now = utcnow()
    result = await db["reports"].update_one(
        {"_id": report_id, "deletedAt": None},
        {"$set": {"deletedAt": now, "updatedAt": now}},
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Report non trovato")
    return {"ok": True}


# ── Email report ───────────────────────────────────────────────
@router.post("/{report_id}/send")
async def send_report_email(
    report_id: str,
    body: ReportSend,
    user: UserRecord = Depends(require_sales),
):
    doc = await db["reports"].find_one({"_id": report_id, "deletedAt": None})
    if not doc:
        raise HTTPException(status_code=404, detail="Report non trovato")

    data = doc.get("data", {})
    kpis = data.get("kpis", {})

    # Build email HTML
    html = f"""
    <h2>{doc.get('title', 'Report CRM')}</h2>
    <p>Generato il {doc.get('createdAt', '').strftime('%d/%m/%Y %H:%M') if isinstance(doc.get('createdAt'), datetime) else 'N/D'}</p>
    {"<p>" + body.message + "</p>" if body.message else ""}

    <h3>KPI Principali</h3>
    <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;">
        <tr><td><b>Lead Totali</b></td><td>{kpis.get('totalLeads', 0)}</td></tr>
        <tr><td><b>Nuovi Lead</b></td><td>{kpis.get('newLeads', 0)}</td></tr>
        <tr><td><b>Deal Attivi</b></td><td>{kpis.get('activeDeals', 0)}</td></tr>
        <tr><td><b>Deal Vinti</b></td><td>{kpis.get('wonDeals', 0)}</td></tr>
        <tr><td><b>Pipeline Value</b></td><td>€{kpis.get('pipelineValue', 0):,.2f}</td></tr>
        <tr><td><b>Revenue</b></td><td>€{kpis.get('revenue', 0):,.2f}</td></tr>
        <tr><td><b>Tasso Conversione</b></td><td>{kpis.get('conversionRate', 0)}%</td></tr>
    </table>
    """

    # Forecast section
    forecast_total = data.get("forecastTotal")
    if forecast_total:
        html += f"""
    <h3>Forecast Pipeline</h3>
    <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;">
        <tr><td><b>Totale Pipeline</b></td><td>€{forecast_total.get('pipeline', 0):,.2f}</td></tr>
        <tr><td><b>Valore Ponderato</b></td><td>€{forecast_total.get('weighted', 0):,.2f}</td></tr>
    </table>
        """

    # Funnel section
    funnel = data.get("funnel")
    if funnel:
        html += "<h3>Funnel Conversioni</h3><table border='1' cellpadding='8' cellspacing='0' style='border-collapse:collapse;'>"
        for item in funnel:
            html += f"<tr><td><b>{item['stage'].title()}</b></td><td>{item['count']}</td></tr>"
        html += "</table>"

    html += """
    <hr>
    <p style="color:#666;font-size:12px;">
        Report generato automaticamente da AiChain CRM<br>
        AiChain Solutions · Catania, Italia
    </p>
    """

    email_id = await send_email(
        to=body.to,
        subject=f"[AiChain CRM] {doc.get('title', 'Report')}",
        html=html,
    )

    if not email_id:
        raise HTTPException(status_code=500, detail="Errore nell'invio dell'email")

    return {"ok": True, "emailId": email_id}