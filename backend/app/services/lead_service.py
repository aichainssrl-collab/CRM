from typing import Optional, List, Dict, Any
import csv
import io
from app.schemas.lead import LeadCreate, LeadUpdate, LeadStageUpdate
from app.services.db_service import (
    create_document, update_document, get_document,
    list_collection, soft_delete, utcnow, new_id,
)
from app.services.activity_service import append_activity
from app.firebase_admin import db
from google.cloud.firestore_v1 import FieldFilter


class LeadService:

    async def find_by_email(self, email: str) -> Optional[dict]:
        query = (
            db.collection("leads")
            .where(filter=FieldFilter("email", "==", email))
            .where(filter=FieldFilter("deletedAt", "==", None))
            .limit(1)
        )
        async for snap in query.stream():
            return {"id": snap.id, **snap.to_dict()}
        return None

    async def create_lead(self, data: LeadCreate, created_by: str) -> dict:
        lead_data = data.model_dump()
        lead_data["assignedTo"] = created_by
        lead_data["activityCount"] = 0
        lead_data["taskCount"] = 0
        lead = await create_document("leads", lead_data)
        await append_activity(lead["id"], {
            "type": "note",
            "title": "Lead creato",
            "userId": created_by,
        })
        return lead

    async def get_lead(self, lead_id: str) -> Optional[dict]:
        return await get_document("leads", lead_id)

    async def get_lead_with_activities(self, lead_id: str) -> Optional[dict]:
        lead = await get_document("leads", lead_id)
        if not lead:
            return None
        activities = []
        query = (
            db.collection("leads")
            .document(lead_id)
            .collection("activities")
            .order_by("createdAt", direction="DESCENDING")
            .limit(50)
        )
        async for snap in query.stream():
            activities.append({"id": snap.id, **snap.to_dict()})
        lead["activities"] = activities
        return lead

    async def update_lead(self, lead_id: str, data: LeadUpdate, updated_by: str) -> Optional[dict]:
        update_data = data.model_dump(exclude_unset=True)
        return await update_document("leads", lead_id, update_data)

    async def update_stage(self, lead_id: str, data: LeadStageUpdate, updated_by: str) -> Optional[dict]:
        update_data = data.model_dump(exclude_unset=True)
        updated = await update_document("leads", lead_id, update_data)
        await append_activity(lead_id, {
            "type": "stage_changed",
            "title": f"Stadio aggiornato a {data.pipelineStage}",
            "userId": updated_by,
            "metadata": {"to": data.pipelineStage},
        })
        return updated

    async def list_leads(
        self,
        status: str = None,
        pipeline_stage: str = None,
        assigned_to: str = None,
        limit: int = 20,
        last_doc_id: str = None,
    ) -> list[dict]:
        filters = []
        if status:
            filters.append(("status", "==", status))
        if pipeline_stage:
            filters.append(("pipelineStage", "==", pipeline_stage))
        if assigned_to:
            filters.append(("assignedTo", "==", assigned_to))
        return await list_collection(
            "leads",
            filters=filters,
            order_by="createdAt",
            descending=True,
            limit=limit,
            last_doc_id=last_doc_id,
        )

    async def delete_lead(self, lead_id: str) -> None:
        await soft_delete("leads", lead_id)

    async def create_or_update_from_form(
        self, email: str, form_data: dict, form_type: str,
        source: str, ip: str, user_agent: str,
    ) -> dict:
        existing = await self.find_by_email(email)
        if existing:
            update = {"source": source}
            if "firstName" in form_data:
                update["firstName"] = form_data["firstName"]
            if "lastName" in form_data:
                update["lastName"] = form_data["lastName"]
            lead = await update_document("leads", existing["id"], update)
        else:
            payload = {
                "email": email,
                "source": source,
                "activityCount": 0,
                "taskCount": 0,
                **{k: v for k, v in form_data.items() if k not in ("consent_given", "consent_text")},
            }
            lead = await create_document("leads", payload)

        await append_activity(lead["id"], {
            "type": "form_submitted",
            "title": f"Form inviato: {form_type}",
            "metadata": {"formType": form_type, "ip": ip, "userAgent": user_agent},
        })
        return lead

    async def import_csv(self, csv_content: str, created_by: str) -> Dict[str, Any]:
        results = {
            "total": 0,
            "imported": 0,
            "skipped": 0,
            "errors": []
        }
        
        reader = csv.DictReader(io.StringIO(csv_content))
        
        for row in reader:
            results["total"] += 1
            try:
                email = row.get("email")
                if not email:
                    results["errors"].append(f"Riga {results['total']}: Email mancante")
                    results["skipped"] += 1
                    continue
                
                existing = await self.find_by_email(email)
                if existing:
                    results["skipped"] += 1
                    continue
                
                lead_data = LeadCreate(
                    email=email,
                    firstName=row.get("first_name"),
                    lastName=row.get("last_name"),
                    phone=row.get("phone_number"),
                    companyName=row.get("company_name"),
                    source="csv_import"
                )
                
                await self.create_lead(lead_data, created_by)
                results["imported"] += 1
                
            except Exception as e:
                results["errors"].append(f"Riga {results['total']}: {str(e)}")
                results["skipped"] += 1
        
        return results
