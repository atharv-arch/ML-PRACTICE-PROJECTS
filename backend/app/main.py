"""
FastAPI Application Entry Point.

Configures the app, mounts routers, serves the static frontend,
and initializes the database on startup.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import init_db
from app.routers import tasks, analytics, suggestions

# ── App Configuration ──────────────────────────────────────────────────────

app = FastAPI(
    title="Daily Routine Optimizer",
    description="An intelligent productivity app that learns your patterns and optimizes your schedule.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS Middleware ────────────────────────────────────────────────────────
# Allow all origins for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register API Routers ──────────────────────────────────────────────────
app.include_router(tasks.router)
app.include_router(analytics.router)
app.include_router(suggestions.router)

# ── Serve Static Frontend ─────────────────────────────────────────────────
# Mount the frontend directory to serve HTML/CSS/JS files
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend")

if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
async def serve_frontend():
    """Serve the main frontend HTML file."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Daily Routine Optimizer API", "docs": "/docs"}


# ── Startup Event ─────────────────────────────────────────────────────────

@app.on_event("startup")
def on_startup():
    """Initialize the database tables on app startup."""
    init_db()
    print("✅ Database initialized")
    print("🚀 Daily Routine Optimizer is running!")
    print("📊 API docs: http://localhost:8000/docs")
    print("🌐 Frontend: http://localhost:8000/")


# ── Health Check ──────────────────────────────────────────────────────────

@app.get("/api/health")
def health_check():
    """Simple health check endpoint for monitoring."""
    return {"status": "healthy", "app": "Daily Routine Optimizer", "version": "1.0.0"}
