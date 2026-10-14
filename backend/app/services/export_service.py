"""
Export service — CSV generation for leads and deals.
"""
import csv
import io
from typing import Optional
from app.services.db_service import db


def _safe_cell(value) -> str:
    """Neutralizza formule CSV (=, +, -, @) per evitare injection all'apertura in Excel."""
    if value is None:
        return ""
    s = str(value)
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + s
    return s


async def export_leads_csv(filters: Optional[dict] = None) -> str:
    """Export leads as CSV string."""
    query = {"deletedAt": None}
    if filters:
        query.update(filters)

    cursor = db["leads"].find(query).sort("createdAt", -1)
    leads = await cursor.to_list(length=10000)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Nome", "Cognome", "Email", "Telefono", "Azienda",
        "Settore", "Fonte", "Stato", "Score", "Assegnato a",
        "Creato il", "Aggiornato il",
    ])

    for lead in leads:
        writer.writerow([
            _safe_cell(lead["_id"]),
            _safe_cell(lead.get("firstName", "")),
            _safe_cell(lead.get("lastName", "")),
            _safe_cell(lead.get("email", "")),
            _safe_cell(lead.get("phone", "")),
            _safe_cell(lead.get("companyName", "")),
            _safe_cell(lead.get("industry", "")),
            _safe_cell(lead.get("source", "")),
            _safe_cell(lead.get("status", "")),
            _safe_cell(lead.get("leadScore", "")),
            _safe_cell(lead.get("assignedTo", "")),
            _safe_cell(lead.get("createdAt", "")),
            _safe_cell(lead.get("updatedAt", "")),
        ])

    return output.getvalue()


async def export_deals_csv(filters: Optional[dict] = None) -> str:
    """Export deals as CSV string."""
    query = {"deletedAt": None}
    if filters:
        query.update(filters)

    cursor = db["deals"].find(query).sort("createdAt", -1)
    deals = await cursor.to_list(length=10000)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Titolo", "Valore", "Probabilità", "Stage",
        "Prodotto", "Note", "Assegnato a", "Scadenza prevista",
        "Creato il", "Chiuso il",
    ])

    for deal in deals:
        writer.writerow([
            _safe_cell(deal["_id"]),
            _safe_cell(deal.get("title", "")),
            _safe_cell(deal.get("value", "")),
            _safe_cell(deal.get("probability", "")),
            _safe_cell(deal.get("stage", "")),
            _safe_cell(deal.get("product", "")),
            _safe_cell(deal.get("notes", "")),
            _safe_cell(deal.get("assignedTo", "")),
            _safe_cell(deal.get("expectedClose", "")),
            _safe_cell(deal.get("createdAt", "")),
            _safe_cell(deal.get("closedAt", "")),
        ])

    return output.getvalue()


async def export_contacts_csv() -> str:
    """Export all contacts (leads with contact info) as CSV."""
    cursor = db["leads"].find({"deletedAt": None}).sort("lastName", 1)
    leads = await cursor.to_list(length=10000)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Email", "Nome", "Cognome", "Azienda", "Telefono", "Settore", "Status"])

    for lead in leads:
        writer.writerow([
            _safe_cell(lead.get("email", "")),
            _safe_cell(lead.get("firstName", "")),
            _safe_cell(lead.get("lastName", "")),
            _safe_cell(lead.get("companyName", "")),
            _safe_cell(lead.get("phone", "")),
            _safe_cell(lead.get("industry", "")),
            _safe_cell(lead.get("status", "")),
        ])

    return output.getvalue()