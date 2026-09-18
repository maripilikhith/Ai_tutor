"""
AI Study Companion — FastAPI Application Entry Point

Creates the FastAPI app, registers all feature routers,
configures middleware (CORS, auth), and defines startup/shutdown events.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings


def create_app() -> FastAPI:
    """Factory function to create and configure the FastAPI application."""

    settings = get_settings()

    app = FastAPI(
        title="AI Study Companion",
        description="AI-powered learning workspace API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── CORS Middleware ──
    # Allow all origins for the portfolio/assignment deployment to prevent Vercel preview domain issues
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Register Feature Routers ──
    _register_routers(app)

    # ── Startup & Shutdown Events ──
    import asyncio
    from app.workers.runner import run_worker

    # Store background tasks so we can cancel them gracefully
    app.state.background_tasks = set()

    @app.on_event("startup")
    async def on_startup():
        """Initialize connections and start background worker."""
        # Build the 'second lane' on the highway
        worker_task = asyncio.create_task(run_worker(poll_interval=10))
        app.state.background_tasks.add(worker_task)

    @app.on_event("shutdown")
    async def on_shutdown():
        """Clean up connections on app shutdown."""
        for task in app.state.background_tasks:
            task.cancel()

    return app


def _register_routers(app: FastAPI) -> None:
    """Register all feature routers with the app."""

    # Health check (always available, no prefix)
    from app.features._health.router import router as health_router
    app.include_router(health_router, tags=["Health"])

    # Home dashboard
    from app.features.home.router import router as home_router
    app.include_router(home_router, tags=["Home"])

    # ── CRUD Features ──
    from app.features.spaces.router import router as spaces_router
    app.include_router(spaces_router, prefix="/api", tags=["Spaces"])

    from app.features.projects.router import router as projects_router
    app.include_router(projects_router, prefix="/api", tags=["Projects"])

    from app.features.materials.router import router as materials_router
    app.include_router(materials_router, prefix="/api", tags=["Materials"])

    # ── AI Features ──
    from app.features.tutor.router import router as tutor_router
    app.include_router(tutor_router, prefix="/api", tags=["AI Tutor"])

    from app.features.quiz.router import router as quiz_router
    app.include_router(quiz_router, prefix="/api", tags=["Quiz"])

    # ── Intelligence Features ──
    from app.features.mastery.router import router as mastery_router
    app.include_router(mastery_router, prefix="/api", tags=["Mastery"])

    from app.features.recommendations.router import router as rec_router
    app.include_router(rec_router, prefix="/api", tags=["Recommendations"])

    from app.features.analytics.router import router as analytics_router
    app.include_router(analytics_router, prefix="/api", tags=["Analytics"])

    # ── Admin (admin-only) ──
    from app.features.admin.router import router as admin_router
    app.include_router(admin_router, prefix="/api", tags=["Admin"])

    # ── User Profile ──
    from app.features.profile.router import router as profile_router
    app.include_router(profile_router, prefix="/api", tags=["Profile"])


# Create the app instance that uvicorn will serve
app = create_app()
