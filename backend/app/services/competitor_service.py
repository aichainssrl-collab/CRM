"""
Competitor intelligence — storage, scrape/monitor, change detection.
"""
from typing import Optional
import hashlib
import logging
import re
from html.parser import HTMLParser

import httpx

from app.services.db_service import db, new_id, utcnow, _to_dict

logger = logging.getLogger(__name__)

PRICE_RE = re.compile(
    r"(?:€|EUR|USD|\$)\s?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?|\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?\s?(?:€|EUR)",
    re.I,
)
PRICING_HINTS = (
    "prezz", "pric", "cost", "pian", "abbonament", "subscription",
    "mensil", "monthly", "annual", "gratis", "free", "trial", "demo",
)
_HINT_LABELS = {
    "prezz": "prezzo",
    "pric": "pricing",
    "cost": "costo",
    "pian": "piano",
    "abbonament": "abbonamento",
    "subscription": "subscription",
    "mensil": "mensile",
    "monthly": "monthly",
    "annual": "annuale",
    "gratis": "gratis",
    "free": "free",
    "trial": "trial",
    "demo": "demo",
}


class _HTMLExtract(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.meta_description = ""
        self.headings: list[str] = []
        self._in_title = False
        self._heading_tag: str | None = None
        self._heading_buf: list[str] = []
        self.text_parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "title":
            self._in_title = True
        elif tag == "meta" and (attrs.get("name") or "").lower() == "description":
            self.meta_description = attrs.get("content") or ""
        elif tag in ("h1", "h2", "h3"):
            self._heading_tag = tag
            self._heading_buf = []
        elif tag == "p":
            self.text_parts.append("")

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == self._heading_tag:
            text = "".join(self._heading_buf).strip()
            if text:
                self.headings.append(text)
            self._heading_tag = None

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._heading_tag:
            self._heading_buf.append(data)
        if data.strip():
            self.text_parts.append(data)


def extract_signals(html: str) -> dict:
    """Parse HTML → structured competitive signals (pure stdlib)."""
    parser = _HTMLExtract()
    try:
        parser.feed(html or "")
    except Exception:
        pass

    body = " ".join(t for t in parser.text_parts if t).strip()
    body_norm = re.sub(r"\s+", " ", body)
    prices = list(dict.fromkeys(PRICE_RE.findall(html or "")))[:20]
    lower = (html or "").lower()
    hints = [_HINT_LABELS[h] for h in PRICING_HINTS if h in lower]

    body_hash = hashlib.sha256(body_norm.encode("utf-8", "ignore")).hexdigest()
    return {
        "title": (parser.title or "").strip()[:300],
        "metaDescription": (parser.meta_description or "").strip()[:500],
        "headings": parser.headings[:30],
        "pricingMentions": prices,
        "pricingKeywords": hints,
        "bodyExcerpt": body_norm[:1500],
        "bodyHash": body_hash,
    }


def diff_signals(prev: dict | None, curr: dict) -> list[dict]:
    """Field-level changes between two signal snapshots."""
    if not prev:
        return []
    changes = []
    for field in ("title", "metaDescription", "bodyHash"):
        before, after = prev.get(field), curr.get(field)
        if before != after:
            changes.append({"field": field, "from": before or "", "to": after or ""})

    prev_head = prev.get("headings") or []
    curr_head = curr.get("headings") or []
    if prev_head != curr_head:
        changes.append(
            {
                "field": "headings",
                "from": " | ".join(prev_head[:10]),
                "to": " | ".join(curr_head[:10]),
            }
        )

    prev_prices = set(prev.get("pricingMentions") or [])
    curr_prices = set(curr.get("pricingMentions") or [])
    if prev_prices != curr_prices:
        changes.append(
            {
                "field": "pricingMentions",
                "from": ", ".join(sorted(prev_prices)),
                "to": ", ".join(sorted(curr_prices)),
            }
        )
    return changes


# ── CRUD ─────────────────────────────────────────────────────────

async def create_competitor(data: dict, created_by: str) -> dict:
    now = utcnow()
    doc = {
        "_id": new_id(),
        "name": data["name"],
        "website": data.get("website", ""),
        "description": data.get("description", ""),
        "tags": data.get("tags") or [],
        "status": "active",
        "lastCheckedAt": None,
        "lastChangeAt": None,
        "changeCount": 0,
        "createdBy": created_by,
        "createdAt": now,
        "updatedAt": now,
        "deletedAt": None,
    }
    await db["competitors"].insert_one(doc)
    return _to_dict(doc)


async def list_competitors(status: Optional[str] = None, tag: Optional[str] = None) -> list[dict]:
    query: dict = {"deletedAt": None}
    if status:
        query["status"] = status
    if tag:
        query["tags"] = tag
    cursor = db["competitors"].find(query).sort("updatedAt", -1)
    docs = await cursor.to_list(length=200)
    return [_to_dict(d) for d in docs]


async def get_competitor(competitor_id: str) -> Optional[dict]:
    doc = await db["competitors"].find_one({"_id": competitor_id, "deletedAt": None})
    return _to_dict(doc) if doc else None


async def update_competitor(competitor_id: str, data: dict) -> Optional[dict]:
    data["updatedAt"] = utcnow()
    doc = await db["competitors"].find_one_and_update(
        {"_id": competitor_id, "deletedAt": None},
        {"$set": data},
        return_document=True,
    )
    return _to_dict(doc) if doc else None


async def delete_competitor(competitor_id: str) -> bool:
    result = await db["competitors"].update_one(
        {"_id": competitor_id, "deletedAt": None},
        {"$set": {"deletedAt": utcnow(), "updatedAt": utcnow()}},
    )
    return result.modified_count > 0


# ── Snapshots & changes ──────────────────────────────────────────

async def latest_snapshot(competitor_id: str) -> Optional[dict]:
    doc = await db["competitor_snapshots"].find_one(
        {"competitorId": competitor_id},
        sort=[("capturedAt", -1)],
    )
    return _to_dict(doc) if doc else None


async def list_snapshots(competitor_id: str, limit: int = 20) -> list[dict]:
    cursor = (
        db["competitor_snapshots"]
        .find({"competitorId": competitor_id})
        .sort("capturedAt", -1)
        .limit(limit)
    )
    docs = await cursor.to_list(length=limit)
    return [_to_dict(d) for d in docs]


async def list_changes(competitor_id: Optional[str] = None, limit: int = 50) -> list[dict]:
    query: dict = {}
    if competitor_id:
        query["competitorId"] = competitor_id
    cursor = db["competitor_changes"].find(query).sort("detectedAt", -1).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [_to_dict(d) for d in docs]


# ── Fetch + scan ─────────────────────────────────────────────────

async def fetch_html(url: str) -> str:
    if not re.match(r"^https?://", url, re.I):
        url = f"https://{url}"
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        resp = await client.get(
            url,
            headers={"User-Agent": "AiChainCRM-CompetitorIntel/1.0"},
        )
        resp.raise_for_status()
        return resp.text


async def scan_competitor(competitor_id: str, html: Optional[str] = None) -> dict:
    """
    Fetch (or accept) HTML, store a snapshot, detect changes vs previous.
    Returns {snapshot, changes}.
    """
    comp = await get_competitor(competitor_id)
    if not comp:
        return {}

    if html is None:
        if not comp.get("website"):
            raise ValueError("Competitor has no website")
        html = await fetch_html(comp["website"])

    signals = extract_signals(html)
    prev = await latest_snapshot(competitor_id)
    changes = diff_signals(prev, signals)

    now = utcnow()
    snapshot = {
        "_id": new_id(),
        "competitorId": competitor_id,
        "url": comp.get("website", ""),
        **signals,
        "capturedAt": now,
        "createdAt": now,
        "updatedAt": now,
        "deletedAt": None,
    }
    await db["competitor_snapshots"].insert_one(snapshot)

    change_docs = []
    if changes:
        for ch in changes:
            change_doc = {
                "_id": new_id(),
                "competitorId": competitor_id,
                "snapshotId": snapshot["_id"],
                "previousSnapshotId": prev.get("id") if prev else None,
                **ch,
                "detectedAt": now,
                "createdAt": now,
                "updatedAt": now,
                "deletedAt": None,
            }
            await db["competitor_changes"].insert_one(change_doc)
            change_docs.append(_to_dict(change_doc))

    update = {
        "lastCheckedAt": now,
        "updatedAt": now,
        "lastSnapshotId": snapshot["_id"],
    }
    if changes:
        update["lastChangeAt"] = now
    await db["competitors"].update_one(
        {"_id": competitor_id},
        {"$set": update, "$inc": {"changeCount": len(changes)}},
    )

    return {"snapshot": _to_dict(snapshot), "changes": change_docs}


async def scan_all() -> list[dict]:
    competitors = await list_competitors(status="active")
    results = []
    for comp in competitors:
        try:
            result = await scan_competitor(comp["id"])
            results.append(
                {
                    "competitorId": comp["id"],
                    "ok": True,
                    "changes": len(result.get("changes") or []),
                }
            )
        except Exception as exc:
            logger.warning("scan_all %s failed: %s", comp.get("name"), exc)
            results.append(
                {"competitorId": comp["id"], "ok": False, "error": str(exc)}
            )
    return results


async def competitor_stats() -> dict:
    total = await db["competitors"].count_documents({"deletedAt": None})
    active = await db["competitors"].count_documents(
        {"deletedAt": None, "status": "active"}
    )
    changes = await db["competitor_changes"].count_documents({"deletedAt": None})
    snapshots = await db["competitor_snapshots"].count_documents({"deletedAt": None})
    return {
        "totalCount": total,
        "activeCount": active,
        "changeCount": changes,
        "snapshotCount": snapshots,
    }
