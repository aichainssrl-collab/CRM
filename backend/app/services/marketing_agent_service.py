"""
Marketing Agent Service — multi-provider LLM (OpenAI, Claude, Gemini, Mistral, custom).
Carica skill di mercato come system context e costruisce un prompt arricchito con dati CRM.
"""
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import litellm
from app.config import settings
from app.services.db_service import db

logger = logging.getLogger(__name__)

# ── Config litellm ─────────────────────────────────────────────────────────────

litellm.drop_params = True  # ignora parametri non supportati dal provider


def _get_llm_config() -> dict:
    """Ritorna i parametri base per litellm.acompletion in base al provider configurato."""
    provider = settings.LLM_PROVIDER.lower()
    model = settings.LLM_MODEL

    config = {"model": model}

    if provider == "openai":
        config["api_key"] = settings.OPENAI_API_KEY
    elif provider == "anthropic":
        config["api_key"] = settings.ANTHROPIC_API_KEY
        if not model.startswith("claude"):
            config["model"] = f"anthropic/{model}"
    elif provider == "gemini":
        config["api_key"] = settings.GEMINI_API_KEY
        if not model.startswith("gemini"):
            config["model"] = f"gemini/{model}"
    elif provider == "ollama":
        config["model"] = f"ollama/{model}"
        config["api_base"] = settings.LLM_LOCAL_BASE_URL
        config["api_key"] = "ollama"
    elif provider == "custom":
        if settings.LLM_BASE_URL:
            config["api_base"] = settings.LLM_BASE_URL
        config["api_key"] = settings.OPENAI_API_KEY or "no-key"

    return config


def _get_local_llm_config() -> dict:
    """Config per il modello locale (Ollama) — task leggeri, zero costo."""
    return {
        "model": f"ollama/{settings.LLM_LOCAL_MODEL}",
        "api_base": settings.LLM_LOCAL_BASE_URL,
        "api_key": "ollama",
    }


# ── Skills ─────────────────────────────────────────────────────────────────────

SKILLS_TO_LOAD = [
    "content-strategy",
    "emails",
    "copywriting",
    "social",
    "ads",
]

SYSTEM_PROMPT_BASE = """Sei l'AI Marketing Agent di AiChain Solutions — un consulente marketing esperto
specializzato in B2B tech, legal tech, FinTech e PA italiana.

Il tuo ruolo:
- Aiutare il team a creare contenuti, strategie email, campagne ads e copy persuasivi
- Usare la conoscenza dei lead e deal del CRM per personalizzare i suggerimenti
- Rispondere sempre in italiano salvo richiesta diversa
- Essere conciso, actionable, orientato ai risultati

Prodotti AiChain che promuovi:
- ZenTratto: RAG documentale per studi legali e professionisti
- SignSiSure: firma digitale eIDAS 2.0 + blockchain
- Enterprise Agent: classificazione e workflow documentali AI

Formato risposte:
- Usa markdown per struttura (headers, bullet, bold)
- Per contenuti generati, usa code block con etichetta del tipo
- Suggerisci sempre una CTA quando appropriato
"""


async def load_skill_context(skills_dir: str) -> str:
    """Carica le SKILL.md dei 5 skill core come contesto aggiuntivo."""
    sections = []
    base = Path(skills_dir)
    if not base.exists():
        logger.warning(f"Skills directory not found: {skills_dir}")
        return ""

    for skill_name in SKILLS_TO_LOAD:
        skill_file = base / skill_name / "SKILL.md"
        if skill_file.exists():
            try:
                content = skill_file.read_text(encoding="utf-8")
                if len(content) > 2000:
                    content = content[:2000] + "\n... (troncato)"
                sections.append(f"### Skill: {skill_name}\n{content}")
            except Exception as e:
                logger.warning(f"Error loading skill {skill_name}: {e}")

    if sections:
        return "\n\n---\n\n".join(sections)
    return ""


# ── CRM Context ────────────────────────────────────────────────────────────────

async def build_crm_context(limit_leads: int = 20, limit_deals: int = 10) -> str:
    """Estrae dati aggregati dal CRM per dare contesto all'agente."""
    sections = []

    try:
        total_leads = await db["leads"].count_documents({"deletedAt": None})
        sections.append(f"Lead totali nel CRM: {total_leads}")

        cursor = db["leads"].find(
            {"deletedAt": None},
            {"firstName": 1, "lastName": 1, "companyName": 1, "status": 1, "tags": 1, "source": 1}
        ).sort("createdAt", -1).limit(limit_leads)
        recent_leads = await cursor.to_list(length=limit_leads)
        if recent_leads:
            leads_summary = []
            for l in recent_leads:
                name = f"{l.get('firstName', '')} {l.get('lastName', '')}".strip()
                company = l.get("companyName", "")
                status = l.get("status", "")
                tags = ", ".join(l.get("tags", []))
                leads_summary.append(f"  - {name} ({company}) — status: {status}, tags: [{tags}]")
            sections.append(f"Ultimi {len(recent_leads)} lead:\n" + "\n".join(leads_summary))

        cursor_deals = db["deals"].find(
            {"deletedAt": None},
            {"name": 1, "value": 1, "stage": 1, "leadId": 1}
        ).sort("createdAt", -1).limit(limit_deals)
        recent_deals = await cursor_deals.to_list(length=limit_deals)
        if recent_deals:
            deals_summary = []
            for d in recent_deals:
                deals_summary.append(
                    f"  - {d.get('name', 'N/D')} — valore: €{d.get('value', 0):,.0f}, stage: {d.get('stage', '')}"
                )
            sections.append(f"Deal attivi:\n" + "\n".join(deals_summary))

        pipeline = [
            {"$match": {"deletedAt": None}},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        status_dist = []
        async for doc in db["leads"].aggregate(pipeline):
            status_dist.append(f"  - {doc['_id'] or 'unknown'}: {doc['count']}")
        if status_dist:
            sections.append("Distribuzione status lead:\n" + "\n".join(status_dist))

    except Exception as e:
        logger.error(f"Error building CRM context: {e}")
        sections.append("(Dati CRM temporaneamente non disponibili)")

    return "\n\n".join(sections)


async def build_system_context(include_skills: bool = True, include_crm: bool = True) -> str:
    """Costruisce il system prompt completo con skill + dati CRM."""
    parts = [SYSTEM_PROMPT_BASE]

    if include_skills:
        skill_ctx = await load_skill_context(settings.MARKETING_SKILLS_DIR)
        if skill_ctx:
            parts.append(f"\n\n## Conoscenza Marketing (skill di riferimento)\n\n{skill_ctx}")

    if include_crm:
        crm_ctx = await build_crm_context()
        if crm_ctx:
            parts.append(f"\n\n## Dati CRM attuali\n\n{crm_ctx}")

    return "\n".join(parts)


# ── LLM Streaming ──────────────────────────────────────────────────────────────

async def stream_chat(message: str, history: list[dict]):
    """Stream della risposta dell'agente marketing via SSE (multi-provider)."""
    system_ctx = await build_system_context()
    llm_config = _get_llm_config()

    messages = [{"role": "system", "content": system_ctx}]
    messages.extend(history)
    messages.append({"role": "user", "content": message})

    response = await litellm.acompletion(
        **llm_config,
        messages=messages,
        stream=True,
        max_tokens=2000,
        temperature=0.7,
    )

    async for chunk in response:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content


async def generate_content(content_type: str, topic: str, tone: str, language: str, extra: str = ""):
    """Genera un contenuto marketing specifico (multi-provider)."""
    system_ctx = await build_system_context(include_crm=False)
    llm_config = _get_llm_config()

    type_prompts = {
        "social_post": "Scrivi un post per LinkedIn/Instagram. Include hashtag pertinenti e una CTA chiara.",
        "email": "Scrivi una email marketing completa con oggetto, preview text, corpo email e CTA.",
        "ad_copy": "Scrivi copy per un annuncio Meta/Google Ads. Include headline, description e CTA.",
        "blog_intro": "Scrivi l'introduzione (200-300 parole) di un articolo blog, accattivante e SEO-friendly.",
    }

    type_label = {
        "social_post": "Post Social",
        "email": "Email Marketing",
        "ad_copy": "Ad Copy",
        "blog_intro": "Introduzione Blog",
    }

    prompt = type_prompts.get(content_type, type_prompts["social_post"])

    user_msg = f"""Genera un contenuto di tipo: {type_label.get(content_type, content_type)}

Argomento: {topic}
Tono: {tone}
Lingua: {language}
{f'Contesto aggiuntivo: {extra}' if extra else ''}

{prompt}

Rispondi SOLO con il contenuto generato, pronto per l'uso."""

    messages = [
        {"role": "system", "content": system_ctx},
        {"role": "user", "content": user_msg},
    ]

    response = await litellm.acompletion(
        **llm_config,
        messages=messages,
        stream=True,
        max_tokens=1500,
        temperature=0.7,
    )

    async for chunk in response:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content


# ── Conversations CRUD ─────────────────────────────────────────────────────────

async def save_conversation(user_id: str, title: str, messages: list[dict]) -> dict:
    """Salva una conversazione nel DB."""
    conv_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    doc = {
        "_id": conv_id,
        "userId": user_id,
        "title": title,
        "messages": messages,
        "createdAt": now,
        "updatedAt": now,
    }
    await db["marketing_conversations"].insert_one(doc)
    return doc


async def list_conversations(user_id: str, limit: int = 50) -> list[dict]:
    """Lista le conversazioni dell'utente (senza messaggi, solo metadata)."""
    cursor = db["marketing_conversations"].find(
        {"userId": user_id},
        {"title": 1, "createdAt": 1, "updatedAt": 1, "messageCount": {"$size": "$messages"}},
    ).sort("updatedAt", -1).limit(limit)
    return await cursor.to_list(length=limit)


async def get_conversation(conv_id: str, user_id: str) -> Optional[dict]:
    """Recupera una conversazione completa."""
    return await db["marketing_conversations"].find_one({"_id": conv_id, "userId": user_id})


async def delete_conversation(conv_id: str, user_id: str) -> bool:
    """Elimina una conversazione."""
    result = await db["marketing_conversations"].delete_one({"_id": conv_id, "userId": user_id})
    return result.deleted_count > 0


async def update_conversation(conv_id: str, user_id: str, messages: list[dict]) -> bool:
    """Aggiorna i messaggi di una conversazione esistente."""
    result = await db["marketing_conversations"].update_one(
        {"_id": conv_id, "userId": user_id},
        {"$set": {"messages": messages, "updatedAt": datetime.now(timezone.utc)}},
    )
    return result.modified_count > 0


# ── CRM Insights ───────────────────────────────────────────────────────────────

async def generate_insights() -> dict:
    """Genera insights dal CRM con suggerimenti AI actionable."""
    try:
        # Lead per fonte
        pipeline_source = [
            {"$match": {"deletedAt": None}},
            {"$group": {"_id": "$source", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        sources = []
        async for doc in db["leads"].aggregate(pipeline_source):
            sources.append({"source": doc["_id"] or "unknown", "count": doc["count"]})

        # Lead per status
        pipeline_status = [
            {"$match": {"deletedAt": None}},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        statuses = []
        async for doc in db["leads"].aggregate(pipeline_status):
            statuses.append({"status": doc["_id"] or "unknown", "count": doc["count"]})

        # Deal per stage
        pipeline_deals = [
            {"$match": {"deletedAt": None}},
            {"$group": {"_id": "$stage", "count": {"$sum": 1}, "totalValue": {"$sum": "$value"}}},
            {"$sort": {"totalValue": -1}},
        ]
        deal_stages = []
        async for doc in db["deals"].aggregate(pipeline_deals):
            deal_stages.append({
                "stage": doc["_id"] or "unknown",
                "count": doc["count"],
                "totalValue": round(doc["totalValue"], 2),
            })

        # Lead per tag (top 10)
        pipeline_tags = [
            {"$match": {"deletedAt": None, "tags": {"$exists": True, "$ne": []}}},
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10},
        ]
        top_tags = []
        async for doc in db["leads"].aggregate(pipeline_tags):
            top_tags.append({"tag": doc["_id"], "count": doc["count"]})

        # Lead ultimi 30 giorni vs 30 giorni precedenti
        now = datetime.now(timezone.utc)
        thirty_days_ago = now.replace(day=1)  # semplificato
        pipeline_trend = [
            {"$match": {"deletedAt": None}},
            {"$group": {
                "_id": {
                    "$cond": [
                        {"$gte": ["$createdAt", thirty_days_ago]},
                        "current",
                        "previous",
                    ]
                },
                "count": {"$sum": 1},
            }},
        ]
        trend = {}
        async for doc in db["leads"].aggregate(pipeline_trend):
            trend[doc["_id"]] = doc["count"]

        total_leads = await db["leads"].count_documents({"deletedAt": None})
        total_deals = await db["deals"].count_documents({"deletedAt": None})
        pipeline_value = [
            {"$match": {"deletedAt": None}},
            {"$group": {"_id": None, "total": {"$sum": "$value"}}},
        ]
        deal_value_result = await db["deals"].aggregate(pipeline_value).to_list(1)
        total_deal_value = deal_value_result[0]["total"] if deal_value_result else 0

        return {
            "summary": {
                "totalLeads": total_leads,
                "totalDeals": total_deals,
                "totalDealValue": round(total_deal_value, 2),
                "leadGrowth": trend,
            },
            "leadsBySource": sources,
            "leadsByStatus": statuses,
            "dealsByStage": deal_stages,
            "topTags": top_tags,
        }

    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        return {"error": str(e)}


async def get_smart_suggestions(context: str = "") -> list[str]:
    """Genera suggerimenti intelligenti — usa modello locale Ollama (zero costo)."""
    llm_config = _get_local_llm_config()  # task leggero → Ollama locale

    # Costruisci un mini-context dai dati CRM
    total_leads = await db["leads"].count_documents({"deletedAt": None})
    total_deals = await db["deals"].count_documents({"deletedAt": None})

    # Ultimo lead
    last_lead = await db["leads"].find_one(
        {"deletedAt": None}, sort=[("createdAt", -1)]
    )
    last_lead_info = ""
    if last_lead:
        name = f"{last_lead.get('firstName', '')} {last_lead.get('lastName', '')}".strip()
        last_lead_info = f"Ultimo lead: {name} ({last_lead.get('companyName', 'N/D')}) — status: {last_lead.get('status', '')}"

    prompt = f"""Basandoti sullo stato attuale del CRM, suggerisci 5 azioni marketing concrete e specifiche.

Dati CRM:
- Lead totali: {total_leads}
- Deal totali: {total_deals}
- {last_lead_info}
{f'- Contesto extra: {context}' if context else ''}

Rispondi SOLO con un JSON array di 5 stringhe, ognuna è un suggerimento breve (max 15 parole).
Esempio: ["Crea email nurturing per lead freddi", "Post LinkedIn su caso studio legale"]

Rispondi SOLO con il JSON array, nient'altro."""

    messages = [
        {"role": "system", "content": "Sei un consulente marketing B2B. Rispondi SOLO con JSON valido."},
        {"role": "user", "content": prompt},
    ]

    try:
        response = await litellm.acompletion(
            **llm_config,
            messages=messages,
            stream=False,
            max_tokens=300,
            temperature=0.7,
        )
        content = response.choices[0].message.content.strip()
        # Estrai JSON dall'eventuale markdown code block
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        import json
        suggestions = json.loads(content)
        if isinstance(suggestions, list):
            return [str(s) for s in suggestions[:5]]
    except Exception as e:
        logger.warning(f"Smart suggestions parse error: {e}")

    # Fallback statico
    return [
        "Crea una sequenza email per lead inattivi",
        "Scrivi un post LinkedIn sui risultati clienti",
        "Analizza le fonti lead più performanti",
        "Prepara un case studio per il settore legale",
        "Genera copy per campagna Meta Ads",
    ]


def get_provider_info() -> dict:
    """Ritorna info sul provider LLM configurato."""
    provider = settings.LLM_PROVIDER.lower()
    has_key = False
    if provider == "openai":
        has_key = bool(settings.OPENAI_API_KEY)
    elif provider == "anthropic":
        has_key = bool(settings.ANTHROPIC_API_KEY)
    elif provider == "gemini":
        has_key = bool(settings.GEMINI_API_KEY)
    elif provider == "ollama":
        has_key = True  # locale, sempre disponibile
    elif provider == "custom":
        has_key = bool(settings.OPENAI_API_KEY)

    return {
        "provider": provider,
        "model": settings.LLM_MODEL,
        "hasKey": has_key,
        "local": {
            "provider": settings.LLM_LOCAL_PROVIDER,
            "model": settings.LLM_LOCAL_MODEL,
            "baseUrl": settings.LLM_LOCAL_BASE_URL,
            "usedFor": "suggerimenti rapidi (zero costo)",
        },
    }