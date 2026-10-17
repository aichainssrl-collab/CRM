"""
Agent workflows — orchestrazione multi-step (Fase D, pattern Agno Workflow).

Workflow «inbound lead»:
  score → task follow-up → (opzionale) welcome email → suggerimento deal

E team leggero: il CRM Agent può delegare content/insight al Marketing Agent.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from app.services.db_service import db, new_id, utcnow

logger = logging.getLogger(__name__)


async def run_inbound_lead_workflow(
    lead_id: str,
    user_id: str,
    *,
    send_welcome: bool = False,
    create_followup_task: bool = True,
    suggest_deal: bool = True,
) -> dict:
    """
    Orchestrazione post-lead: score, attività, task, suggerimento deal.
    Ritorna {ok, steps[], summary}.
    """
    from app.services.activity_service import append_activity
    from app.services.scoring_service import calculate_lead_score

    lead = await db["leads"].find_one({"_id": lead_id, "deletedAt": None})
    if not lead:
        return {"ok": False, "error": f"Lead non trovato: {lead_id}", "steps": []}

    steps: list[dict] = []
    email = lead.get("email")
    name = f"{lead.get('firstName') or ''} {lead.get('lastName') or ''}".strip() or email

    # 1) Score
    try:
        score = await calculate_lead_score(lead_id)
        steps.append({"tool": "calculate_lead_score", "ok": True, "score": score})
    except Exception as exc:
        score = lead.get("leadScore") or 0
        steps.append({"tool": "calculate_lead_score", "ok": False, "error": str(exc)})

    # 2) Activity breadcrumb
    try:
        await append_activity(lead_id, {
            "type": "note",
            "title": "Workflow inbound lead eseguito",
            "userId": user_id,
            "metadata": {"score": score},
        })
        steps.append({"tool": "append_activity", "ok": True})
    except Exception as exc:
        steps.append({"tool": "append_activity", "ok": False, "error": str(exc)})

    # 3) Follow-up task
    task_id = None
    if create_followup_task:
        try:
            now = utcnow()
            task_id = new_id()
            await db["tasks"].insert_one({
                "_id": task_id,
                "leadId": lead_id,
                "title": f"Follow-up lead {name}",
                "description": f"Lead inbound (score {score}). Contattare entro 24-48h.",
                "dueDate": now,
                "priority": "high" if score >= 60 else "normal",
                "type": "todo",
                "status": "open",
                "assignedTo": user_id,
                "createdBy": user_id,
                "createdAt": now,
                "updatedAt": now,
                "deletedAt": None,
            })
            await db["leads"].update_one({"_id": lead_id}, {"$inc": {"taskCount": 1}})
            steps.append({"tool": "create_task", "ok": True, "taskId": task_id})
        except Exception as exc:
            steps.append({"tool": "create_task", "ok": False, "error": str(exc)})

    # 4) Welcome email (opzionale, best-effort)
    if send_welcome:
        try:
            from app.services.email_service import send_email_ex

            sent = await send_email_ex(
                to=email,
                subject="Grazie per averci contattato — AiChain Solutions",
                html=(
                    f"<p>Ciao {name or ''},</p>"
                    "<p>grazie per l'interesse verso AiChain Solutions. "
                    "Un nostro consulente ti contatterà a breve.</p>"
                    "<p>— Team AiChain</p>"
                ),
            )
            steps.append({"tool": "send_welcome_email", "ok": bool(sent.get("ok")), "mock": sent.get("mock")})
        except Exception as exc:
            steps.append({"tool": "send_welcome_email", "ok": False, "error": str(exc)})

    # 5) Deal suggestion
    deal_hint = None
    if suggest_deal:
        industry = lead.get("industry") or ""
        value = 15000 if score >= 60 else 5000
        deal_hint = {
            "suggestedTitle": f"Opportunità {lead.get('companyName') or name}",
            "suggestedValue": value,
            "suggestedStage": "qualified" if score >= 60 else "new",
            "industry": industry,
        }
        steps.append({"tool": "suggest_deal", "ok": True, **deal_hint})

    ok = all(s.get("ok", True) for s in steps)
    summary = (
        f"Workflow inbound per {name}: score={score}, "
        f"task={'creato' if task_id else 'no'}, "
        f"deal={'da valutare ' + str(deal_hint['suggestedValue']) if deal_hint else 'no'}"
    )
    return {"ok": ok, "steps": steps, "summary": summary, "leadId": lead_id, "score": score, "dealHint": deal_hint}


# ── Team: CRM ↔ Marketing ────────────────────────────────────────────────────

async def marketing_assist(user_id: str, request: str, *, content_type: str = "email", topic: str = "") -> dict:
    """
    Delega al Marketing Agent (genera contenuto o insight) e riporta il risultato al CRM Agent.
    """
    try:
        from app.services import marketing_agent_service as mas

        if request == "insights" or "insight" in (topic or "").lower() or "analisi" in (topic or "").lower():
            insights = await mas.generate_insights()
            return {
                "ok": True,
                "team": "marketing",
                "kind": "insights",
                "message": "Insight marketing generati",
                "insights": insights,
            }

        topic = topic or request or "comunicazione commerciale"
        content = await mas.generate_content(
            content_type=content_type or "email",
            topic=topic,
            tone="professionale",
            language="italiano",
        )
        return {
            "ok": True,
            "team": "marketing",
            "kind": "content",
            "contentType": content_type,
            "topic": topic,
            "message": f"Contenuto marketing generato: «{topic}»",
            "content": content,
        }
    except Exception as exc:
        logger.exception("marketing_assist failed")
        return {"ok": False, "error": str(exc), "team": "marketing"}


# ── MCP-lite manifest ────────────────────────────────────────────────────────

def mcp_tool_manifest(tools: list[dict]) -> dict:
    """
    Manifest stile MCP per esporre i tool CRM a client esterni (Claude, ChatGPT).
    Compatibile in lettura con il formato tools OpenAI/MCP.
    """
    return {
        "protocol": "mcp-lite/0.1",
        "server": "aichain-crm-agent",
        "capabilities": ["tools", "prompts"],
        "tools": [
            {
                "name": t["function"]["name"],
                "description": t["function"].get("description", ""),
                "inputSchema": t["function"].get("parameters", {"type": "object", "properties": {}}),
            }
            for t in tools
        ],
        "prompts": [
            {
                "name": "crm_summary",
                "description": "Riepilogo operativo del CRM",
                "arguments": [],
            },
            {
                "name": "inbound_lead",
                "description": "Workflow completo su un nuovo lead",
                "arguments": [{"name": "leadEmail", "required": True}],
            },
        ],
    }


async def execute_mcp_tool(name: str, arguments: dict, user_id: str, user_role: str = "sales") -> dict:
    from app.services import crm_agent_service as a

    if name == "workflow_inbound_lead":
        lead = await db["leads"].find_one({
            "email": (arguments.get("leadEmail") or "").strip().lower(),
            "deletedAt": None,
        })
        if not lead:
            return {"ok": False, "error": "Lead non trovato"}
        return await run_inbound_lead_workflow(lead["_id"], user_id)

    return await a.run_tool(name, arguments or {}, user_id, user_role=user_role)
