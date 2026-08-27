"""NETRA — FastAPI application entrypoint.

Modular monolith: routers are mounted per capability module.
Golden path (KB file 09 §89): report → incident → zone → priority → recommendation → field verification.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import check_db_health
from app.security.rate import limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.queue.service import start_worker, stop_worker

    start_worker()
    yield
    stop_worker()


app = FastAPI(
    title="NETRA",
    version="0.1.0",
    description="Network-resilient Emergency Triage and Response Assistance — disaster-response intelligence layer.",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz", tags=["system"])
def healthz() -> dict:
    db_ok = check_db_health()
    return {
        "status": "ok" if db_ok else "degraded",
        "database": "healthy" if db_ok else "unavailable",
        "version": app.version,
        "priority_rules": settings.priority_rules_version,
        "nlp_rules": settings.nlp_rules_version,
        "llm_enabled": settings.llm_enabled,
        "llm_model": settings.ai_gateway_model,
    }


# Capability routers are mounted as modules land (auth, ingestion, ...).
# This keeps the monolith modular while the build progresses.
def register_routers() -> None:
    from app.auth.router import router as auth_router
    from app.audit.router import router as audit_router
    from app.clustering.router import router as clustering_router
    from app.ingestion.router import router as ingestion_router
    from app.incidents.router import router as incidents_router
    from app.lifecycle.router import router as lifecycle_router
    from app.priority.router import router as priority_router
    from app.recommend.router import router as recommend_router
    from app.simulation.router import router as simulation_router
    from app.system.router import router as system_router

    app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(ingestion_router, prefix="/api/v1", tags=["events"])
    app.include_router(incidents_router, prefix="/api/v1", tags=["incidents"])
    app.include_router(priority_router, prefix="/api/v1", tags=["priority"])
    app.include_router(clustering_router, prefix="/api/v1", tags=["zones"])
    app.include_router(recommend_router, prefix="/api/v1", tags=["recommendations"])
    app.include_router(lifecycle_router, prefix="/api/v1", tags=["field-updates"])
    app.include_router(simulation_router, prefix="/api/v1/sim", tags=["simulation"])
    app.include_router(system_router, prefix="/api/v1", tags=["system"])
    app.include_router(audit_router, prefix="/api/v1", tags=["audit"])


register_routers()