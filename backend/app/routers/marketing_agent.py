"""
Marketing Agent Router — SSE streaming chat, content gen, conversations, insights, suggestions.
"""
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from app.deps import get_current_user
from app.schemas.marketing_agent import (
    MarketingChatRequest,
    ContentGenerateRequest,
    ConversationSaveRequest,
)
from app.services import marketing_agent_service as svc

logger = logging.getLogger(__name__)
router = APIRouter()


# ── SSE helpers ────────────────────────────────────────────────────────────────

async def _sse_generator(stream):
    """Wrappa un async generator in formato SSE."""
    try:
        async for chunk in stream:
            yield f"data: {json.dumps({'content': chunk})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"
    except Exception as e:
        logger.error(f"SSE stream error: {e}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"


# ── Chat & Content ─────────────────────────────────────────────────────────────

@router.post("/chat")
async def chat_stream(
    req: MarketingChatRequest,
    user=Depends(get_current_user),
):
    """Chat con l'agente marketing — risposta SSE streaming."""
    return StreamingResponse(
        _sse_generator(svc.stream_chat(req.message, req.history)),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/generate")
async def generate_content(
    req: ContentGenerateRequest,
    user=Depends(get_current_user),
):
    """Genera un contenuto marketing — risposta SSE streaming."""
    return StreamingResponse(
        _sse_generator(svc.generate_content(
            content_type=req.type,
            topic=req.topic,
            tone=req.tone,
            language=req.language,
            extra=req.extra_context or "",
        )),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── Conversations CRUD ─────────────────────────────────────────────────────────

@router.post("/conversations")
async def save_conversation(
    req: ConversationSaveRequest,
    user=Depends(get_current_user),
):
    """Salva una conversazione."""
    doc = await svc.save_conversation(
        user_id=user["uid"],
        title=req.title,
        messages=req.messages,
    )
    return {"id": doc["_id"], "title": doc["title"], "createdAt": str(doc["createdAt"])}


@router.get("/conversations")
async def list_conversations(user=Depends(get_current_user)):
    """Lista conversazioni dell'utente."""
    convs = await svc.list_conversations(user["uid"])
    return {"conversations": convs}


@router.get("/conversations/{conv_id}")
async def get_conversation(conv_id: str, user=Depends(get_current_user)):
    """Recupera una conversazione completa."""
    conv = await svc.get_conversation(conv_id, user["uid"])
    if not conv:
        raise HTTPException(status_code=404, detail="Conversazione non trovata")
    return conv


@router.put("/conversations/{conv_id}")
async def update_conversation(
    conv_id: str,
    req: ConversationSaveRequest,
    user=Depends(get_current_user),
):
    """Aggiorna i messaggi di una conversazione."""
    ok = await svc.update_conversation(conv_id, user["uid"], req.messages)
    if not ok:
        raise HTTPException(status_code=404, detail="Conversazione non trovata")
    return {"updated": True}


@router.delete("/conversations/{conv_id}")
async def delete_conversation(conv_id: str, user=Depends(get_current_user)):
    """Elimina una conversazione."""
    ok = await svc.delete_conversation(conv_id, user["uid"])
    if not ok:
        raise HTTPException(status_code=404, detail="Conversazione non trovata")
    return {"deleted": True}


# ── Insights & Suggestions ─────────────────────────────────────────────────────

@router.get("/insights")
async def get_insights(user=Depends(get_current_user)):
    """Insights CRM con analisi aggregata."""
    return await svc.generate_insights()


@router.get("/suggestions")
async def get_suggestions(user=Depends(get_current_user)):
    """Suggerimenti intelligenti dal CRM (modello locale, zero costo)."""
    suggestions = await svc.get_smart_suggestions()
    return {"suggestions": suggestions}


# ── Config info ────────────────────────────────────────────────────────────────

@router.get("/skills")
async def list_skills(user=Depends(get_current_user)):
    """Lista le skill marketing disponibili."""
    return {
        "skills": svc.SKILLS_TO_LOAD,
        "count": len(svc.SKILLS_TO_LOAD),
    }


@router.get("/provider")
async def get_provider(user=Depends(get_current_user)):
    """Info sul provider LLM configurato."""
    return svc.get_provider_info()