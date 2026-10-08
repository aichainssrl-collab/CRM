from app.services.db_service import db, utcnow
from pymongo import DESCENDING

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


async def calculate_lead_score(lead_id: str) -> int:
    lead = await db["leads"].find_one({"_id": lead_id})
    if not lead:
        return 0

    score = 0

    seniority = (lead.get("roleSeniority") or lead.get("roleTitle") or "").lower()
    for key, pts in _SENIORITY_SCORE.items():
        if key in seniority:
            score += pts
            break

    industry = (lead.get("industry") or "").lower()
    for key, pts in _INDUSTRY_SCORE.items():
        if key in industry:
            score += pts
            break

    company_size = (lead.get("companySize") or "").lower()
    for key, pts in _COMPANY_SIZE_SCORE.items():
        if key in company_size:
            score += pts
            break

    activity_bonus = 0
    cursor = (
        db["activities"]
        .find({"leadId": lead_id})
        .sort("createdAt", DESCENDING)
        .limit(50)
    )
    async for act in cursor:
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

    await db["leads"].update_one(
        {"_id": lead_id},
        {"$set": {"leadScore": score, "isQualified": is_qualified, "updatedAt": utcnow()}},
    )
    return score
