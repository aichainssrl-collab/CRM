from typing import Optional, List, Dict, Any
import csv
import io
from app.schemas.lead import LeadCreate, LeadUpdate, LeadStageUpdate
from app.services.db_service import (
    db, create_document, update_document, get_document,
    list_collection, soft_delete, utcnow, new_id,
)
from app.services.activity_service import append_activity
from pymongo import DESCENDING


class LeadService:

    async def find_by_email(self, email: str) -> Optional[dict]:
        doc = await db["leads"].find_one({"email": email, "deletedAt": None})
        if not doc:
            return None
        doc = dict(doc)
        doc["id"] = doc.pop("_id")
        return doc

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
        from app.services.activity_service import list_activities
        lead["activities"] = await list_activities(lead_id)
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
        results = {"total": 0, "imported": 0, "skipped": 0, "errors": []}
        reader = csv.DictReader(io.StringIO(csv_content))

        for row in reader:
            results["total"] += 1
            try:
                email = (row.get("email") or "").strip()
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
                    firstName=row.get("first_name", "").strip() or None,
                    lastName=row.get("last_name", "").strip() or None,
                    phone=row.get("phone_number", "").strip() or None,
                    companyName=row.get("company_name", "").strip() or None,
                    source="csv_import",
                )
                await self.create_lead(lead_data, created_by)
                results["imported"] += 1

            except Exception as e:
                results["errors"].append(f"Riga {results['total']}: {str(e)}")
                results["skipped"] += 1

        return results

    async def import_excel(self, file_bytes: bytes, created_by: str) -> Dict[str, Any]:
        """Importa lead da file .xlsx. Supporta formato standard e formato eventi (TAGS, NOME, COGNOME, RAGIONE SOCIALE)."""
        import openpyxl

        results = {"total": 0, "imported": 0, "skipped": 0, "errors": [], "source": "excel_import"}

        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
        ws = wb.active

        # Read header row to detect format
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return {"total": 0, "imported": 0, "skipped": 0, "errors": ["File vuoto"]}

        headers = [str(h).strip().lower() if h else "" for h in rows[0]]

        # Detect column mapping
        col_map = self._detect_excel_columns(headers)

        for row_idx, row in enumerate(rows[1:], start=2):
            results["total"] += 1
            try:
                vals = {k: (str(row[v]).strip() if v < len(row) and row[v] else "") for k, v in col_map.items()}

                # Generate email placeholder if none present (event lists often lack email)
                email = vals.get("email", "")
                if not email:
                    # Skip rows with no identifying info at all
                    if not vals.get("lastName") and not vals.get("companyName"):
                        results["skipped"] += 1
                        continue
                    # Generate a placeholder email from name/company for dedup
                    slug = (vals.get("lastName", "") or vals.get("companyName", "")).lower().replace(" ", "")
                    email = f"import-{slug}-{row_idx}@placeholder.aichain"

                existing = await self.find_by_email(email)
                if existing:
                    results["skipped"] += 1
                    continue

                tags = []
                raw_tag = vals.get("tags", "")
                if raw_tag:
                    tags = [t.strip() for t in raw_tag.split(",") if t.strip()]

                lead_data = LeadCreate(
                    email=email,
                    firstName=vals.get("firstName") or None,
                    lastName=vals.get("lastName") or None,
                    phone=vals.get("phone") or None,
                    companyName=vals.get("companyName") or None,
                    source="excel_import",
                    tags=tags,
                )
                await self.create_lead(lead_data, created_by)
                results["imported"] += 1

            except Exception as e:
                results["errors"].append(f"Riga {row_idx}: {str(e)}")
                results["skipped"] += 1

        wb.close()
        return results

    @staticmethod
    def _detect_excel_columns(headers: list[str]) -> dict:
        """Rileva automaticamente le colonne del file Excel."""
        mapping = {}
        _ALIASES = {
            "email": ["email", "e-mail", "mail", "email address"],
            "firstName": ["firstName", "first_name", "nome", "first name", "prenom"],
            "lastName": ["lastName", "last_name", "cognome", "last name", "surname", "nom"],
            "phone": ["phone", "phone_number", "telefono", "tel", "cellulare", "mobile"],
            "companyName": ["companyName", "company_name", "company", "ragione sociale", "ragione_sociale", "azienda", "societa", "organization"],
            "tags": ["tags", "tag", "categoria", "category", "tipo"],
        }
        for i, h in enumerate(headers):
            h_lower = h.lower().strip()
            for field, aliases in _ALIASES.items():
                if field not in mapping and h_lower in aliases:
                    mapping[field] = i
                    break
        # Fallback: if only positional (no header match), try standard positions
        if not mapping:
            mapping = {"tags": 0, "firstName": 1, "lastName": 2, "companyName": 3}
        return mapping
