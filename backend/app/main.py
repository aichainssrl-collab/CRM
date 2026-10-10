import logging
import traceback
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.config import settings
from app.limiter import limiter
from app.middleware import SecurityHeadersMiddleware
import app.firebase_admin  # noqa: F401 — inizializza Firebase Auth all'avvio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.routers import (
    leads, forms, auth, activities, tasks, deals, bookings,
    gdpr, users, task_global, dashboard, meta_ads, marketing_agent,
    analytics, reports, email_sequences, notifications, export, admin, calendar,
    products, proposals, workflows, invoices, content, email_templates,
    whatsapp, competitors, apollo,
)
from app.tasks import handlers
from app.services.db_service import db as mongo_db

app = FastAPI(
    title="AiChain CRM API",
    version="2.0.0",
    description="AiChain CRM — Lead Management, GDPR, Forms, Booking, Marketing Agent, Analytics, Email Sequences",
    debug=settings.DEBUG,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security headers (always)
app.add_middleware(SecurityHeadersMiddleware)

# CORS — origins da settings (ALLOWED_ORIGINS env var), fallback localhost per dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers autenticati
app.include_router(auth.router,       prefix="/api/v1/auth",       tags=["auth"])
app.include_router(users.router,      prefix="/api/v1/users",      tags=["users"])
app.include_router(leads.router,      prefix="/api/v1/leads",      tags=["leads"])
app.include_router(activities.router, prefix="/api/v1/leads",      tags=["activities"])
app.include_router(tasks.router,      prefix="/api/v1/leads",      tags=["tasks"])
app.include_router(deals.router,      prefix="/api/v1/deals",      tags=["deals"])
app.include_router(gdpr.router,       prefix="/api/v1/gdpr",       tags=["gdpr"])
app.include_router(task_global.router, prefix="/api/v1/tasks",     tags=["tasks-global"])
app.include_router(dashboard.router,  prefix="/api/v1/dashboard",  tags=["dashboard"])
app.include_router(meta_ads.router,   prefix="/api/v1/meta",        tags=["meta-ads"])
app.include_router(marketing_agent.router, prefix="/api/v1/marketing", tags=["marketing-agent"])
app.include_router(analytics.router,    prefix="/api/v1/analytics",  tags=["analytics"])
app.include_router(reports.router,      prefix="/api/v1/reports",    tags=["reports"])
app.include_router(email_sequences.router, prefix="/api/v1/email-sequences", tags=["email-sequences"])
app.include_router(notifications.router,  prefix="/api/v1/notifications",  tags=["notifications"])
app.include_router(export.router,        prefix="/api/v1/export",       tags=["export"])
app.include_router(admin.router,        prefix="/api/v1/admin",        tags=["admin"])
app.include_router(calendar.router,     prefix="/api/v1/calendar",     tags=["calendar"])
app.include_router(products.router,     prefix="/api/v1/products",     tags=["products"])
app.include_router(products.seg_router, prefix="/api/v1/segments",     tags=["segments"])
app.include_router(proposals.router,    prefix="/api/v1/proposals",    tags=["proposals"])
app.include_router(workflows.router,   prefix="/api/v1/workflows",    tags=["workflows"])
app.include_router(invoices.router,    prefix="/api/v1/invoices",     tags=["invoices"])
app.include_router(content.router,     prefix="/api/v1/content",      tags=["content"])
app.include_router(email_templates.router, prefix="/api/v1/email-templates", tags=["email-templates"])
app.include_router(whatsapp.router, prefix="/api/v1/whatsapp", tags=["whatsapp"])
app.include_router(competitors.router, prefix="/api/v1/competitors", tags=["competitors"])
app.include_router(apollo.router, prefix="/api/v1/apollo", tags=["apollo"])

# Routers pubblici (no auth)
app.include_router(forms.router,    prefix="/api/v1/forms",    tags=["forms"])
app.include_router(bookings.router, prefix="/api/v1/bookings", tags=["bookings"])
app.include_router(whatsapp.public_router, prefix="/api/v1/whatsapp", tags=["whatsapp-webhook"])

# Cloud Tasks handlers (OIDC protected)
app.include_router(handlers.router, prefix="/tasks/handlers", tags=["tasks-internal"])


# Global exception handler — safe response in production
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    logger.error("Unhandled exception on %s %s:\n%s", request.method, request.url.path, tb)
    detail = (
        f"Errore interno: {type(exc).__name__}: {exc}"
        if settings.DEBUG
        else "Errore interno del server"
    )
    return JSONResponse(status_code=500, content={"detail": detail})


# Health check per Cloud Run / Uptime Checks — include MongoDB connectivity
@app.get("/api/health", tags=["Health"])
async def health_check():
    checks = {"api": "ok"}
    try:
        await mongo_db.command("ping")
        checks["mongodb"] = "ok"
        status = "ok"
    except Exception as e:
        checks["mongodb"] = f"error: {type(e).__name__}"
        status = "degraded"
    return {
        "status": status,
        "checks": checks,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": app.version,
    }