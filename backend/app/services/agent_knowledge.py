"""
Agent knowledge — RAG-lite su content library, template, prodotti (Fase F).

Senza vector DB: BM25-ish / keyword scoring su Mongo (indice già presente).
Se in futuro serve embedding, sostituire `search_knowledge` mantenendo la firma.
"""
from __future__ import annotations

import re
from typing import Any


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[\wà-ú]{2,}", (text or "").lower()) if t}


def _score(query_tokens: set[str], *fields: str) -> float:
    if not query_tokens:
        return 0.0
    hits = 0
    for f in fields:
        ft = _tokens(f)
        if not ft:
            continue
        overlap = len(query_tokens & ft)
        # bonus se phrase multi-parola è nel campo
        hits += overlap
    return hits / max(len(query_tokens), 1)


async def search_knowledge(query: str, *, kinds: list[str] | None = None, limit: int = 8) -> dict:
    """
    Cerca knowledge CRM. kinds: content | template | product | lead | deal
    Ritorna {ok, results:[{kind, id, title, snippet, score}]}
    """
    from app.services.db_service import db

    q = (query or "").strip()
    qt = _tokens(q)
    if not qt:
        return {"ok": False, "error": "query obbligatoria"}

    kinds = kinds or ["content", "template", "product"]
    results: list[dict] = []

    async def collect(kind: str, cursor):
        async for d in cursor:
            score = _score(
                qt,
                d.get("title") or d.get("name") or "",
                d.get("description") or d.get("subject") or "",
                (d.get("body") or d.get("bodyHtml") or "")[:2000],
                " ".join(d.get("tags") or []),
            )
            if score <= 0:
                continue
            results.append({
                "kind": kind,
                "id": d["_id"],
                "title": d.get("title") or d.get("name") or d.get("subject"),
                "snippet": (d.get("body") or d.get("bodyHtml") or d.get("description") or "")[:180],
                "score": round(score, 3),
            })

    if "content" in kinds:
        await collect("content", db["content_library"].find({"deletedAt": None}).limit(40))
    if "template" in kinds:
        await collect("template", db["email_templates"].find({"deletedAt": None}).limit(30))
    if "product" in kinds:
        await collect("product", db["products"].find({"deletedAt": None}).limit(30))
    if "lead" in kinds:
        await collect("lead", db["leads"].find({"deletedAt": None}).sort("leadScore", -1).limit(30))
    if "deal" in kinds:
        await collect("deal", db["deals"].find({"deletedAt": None}).limit(30))

    results.sort(key=lambda r: r["score"], reverse=True)
    top = results[:limit]
    return {
        "ok": True,
        "query": q,
        "count": len(top),
        "results": top,
        "message": f"{len(top)} risultati knowledge per «{q}»",
    }
