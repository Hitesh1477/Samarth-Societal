"""
SAMARTH FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.health import router as health_router
from app.api.problems import router as problems_router
from app.api.challenges import router as challenges_router
from app.api.projects import router as projects_router
from app.api.milestones import router as milestones_router
from app.api.pilots_impact import router as pilots_impact_router
from app.api.dashboard import router as dashboard_router
from app.api.map import router as map_router



# ── Lifespan ────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup / shutdown lifecycle hook."""
    print(f"[STARTUP] {settings.APP_NAME} v{settings.APP_VERSION} starting up...")
    yield
    print(f"[SHUTDOWN] {settings.APP_NAME} shutting down...")


# ── App factory ──────────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title="SAMARTH Backend",
        version=settings.APP_VERSION,
        description=(
            "Societal Action for Managing And Resolving Transformative Hackathon — "
            "Backend API connecting citizen reports, AI analysis, and solver matching."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ───────────────────────────────────────────────────────────────────
    app.include_router(health_router)
    app.include_router(problems_router)
    app.include_router(challenges_router)
    app.include_router(projects_router)
    app.include_router(milestones_router)
    app.include_router(pilots_impact_router)
    app.include_router(dashboard_router)
    app.include_router(map_router)


    return app


app = create_app()
