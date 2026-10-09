import logging
import traceback
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.config import settings
from app.limiter import limiter
import app.firebase_admin  # noqa: F401 — inizializza Firebase Auth all'avvio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.routers import leads, forms, auth, activities, tasks, deals, bookings, gdpr, users, task_global, dashboard, meta_ads, marketing_agent, analytics, reports
from app.tasks import handlers

app = FastAPI(
    title="AiChain CRM API",
    version="1.0.0",
    description="Fase 1 — Lead Management, GDPR, Forms, Booking",
    debug=settings.DEBUG,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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

# Routers pubblici (no auth)
app.include_router(forms.router,    prefix="/api/v1/forms",    tags=["forms"])
app.include_router(bookings.router, prefix="/api/v1/bookings", tags=["bookings"])

# Cloud Tasks handlers (OIDC protected)
app.include_router(handlers.router, prefix="/tasks/handlers", tags=["tasks-internal"])


# Global exception handler — logga il traceback completo e ritorna 500 leggibile
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    logger.error("Unhandled exception on %s %s:\n%s", request.method, request.url.path, tb)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Errore interno: {type(exc).__name__}: {exc}"},
    )


# Health check per Cloud Run / Uptime Checks
@app.get("/api/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
