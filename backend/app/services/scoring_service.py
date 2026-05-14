from app.firebase_admin import db
from app.services.db_service import utcnow


_SENIORITY_SCORE = {
    "c-level": 30, "ceo": 30, "cto": 30, "coo": 30, "cfo": 30,
    "vp": 25, "vice president": 25,
    "director": 20, "direttore": 20,
    "manager": 15, "responsabile": 15,
    "senior": 10,
}

_INDUSTRY_SCORE = {
    "legal": 20, "legale": 20, "finance": 15, "finanza": 15,
    "banking": 15, "insurance": 15, "assicurazioni": 15,
    "tech": 10, "technology": 10, "software": 10,
    "consulting": 10, "consulenza": 10,
    "manufacturing": 8, "retail": 5,
}

_COMPANY_SIZE_SCORE = {
    "1-10": 5, "11-50": 10, "51-200": 15,
    "201-1000": 20, "201-500": 20, "501-1000": 20,
    "1001+": 25, "1000+": 25,
}


async def calculate_lead_score(lead_id: str, db_client=None) -> int:
    """
    Calcola score 0-100 in base a dati demografici + attività.
    isQualified = True se score >= 60.
    """
    client = db_client or db
    snap = await client.collection("leads").document(lead_id).get()
    if not snap.exists:
        return 0

    lead = snap.to_dict()
    score = 0

    # Seniority (max 30)
    seniority = (lead.get("roleSeniority") or lead.get("roleTitle") or "").lower()
    for key, pts in _SENIORITY_SCORE.items():
        if key in seniority:
            score += pts
            break

    # Industry (max 20)
    industry = (lead.get("industry") or "").lower()
    for key, pts in _INDUSTRY_SCORE.items():
        if key in industry:
            score += pts
            break

    # Company size (max 25)
    company_size = (lead.get("companySize") or "").lower()
    for key, pts in _COMPANY_SIZE_SCORE.items():
        if key in company_size:
            score += pts
            break

    # Attività comportamentali (max 40)
    activities_query = (
        client.collection("leads")
        .document(lead_id)
        .collection("activities")
        .order_by("createdAt", direction="DESCENDING")
        .limit(50)
    )
    activity_bonus = 0
    async for act_snap in activities_query.stream():
        act = act_snap.to_dict()
        act_type = act.get("type", "")
        form_type = (act.get("metadata") or {}).get("formType", "")

        if act_type == "form_submitted":
            if "booking" in form_type or "demo" in form_type:
                activity_bonus = max(activity_bonus, 40)
            elif "assessment" in form_type:
                activity_bonus = max(activity_bonus, 25)
            elif "playbook" in form_type:
                activity_bonus = max(activity_bonus, 10)
            else:
                activity_bonus = max(activity_bonus, 5)

    score = min(100, score + activity_bonus)
    is_qualified = score >= 60

    await client.collection("leads").document(lead_id).update({
        "leadScore": score,
        "isQualified": is_qualified,
        "updatedAt": utcnow(),
    })
    return score
