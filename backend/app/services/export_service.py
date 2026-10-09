"""
Export service — CSV generation for leads and deals.
"""
import csv
import io
from typing import Optional
from app.services.db_service import db


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
            lead["_id"],
            lead.get("firstName", ""),
            lead.get("lastName", ""),
            lead.get("email", ""),
            lead.get("phone", ""),
            lead.get("companyName", ""),
            lead.get("industry", ""),
            lead.get("source", ""),
            lead.get("status", ""),
            lead.get("leadScore", ""),
            lead.get("assignedTo", ""),
            lead.get("createdAt", ""),
            lead.get("updatedAt", ""),
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
            deal["_id"],
            deal.get("title", ""),
            deal.get("value", ""),
            deal.get("probability", ""),
            deal.get("stage", ""),
            deal.get("product", ""),
            deal.get("notes", ""),
            deal.get("assignedTo", ""),
            deal.get("expectedClose", ""),
            deal.get("createdAt", ""),
            deal.get("closedAt", ""),
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
            lead.get("email", ""),
            lead.get("firstName", ""),
            lead.get("lastName", ""),
            lead.get("companyName", ""),
            lead.get("phone", ""),
            lead.get("industry", ""),
            lead.get("status", ""),
        ])

    return output.getvalue()