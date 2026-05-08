"""UAP NEXUS FastAPI application."""
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import incidents, documents, crawler, alerts

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle."""
    try:
        from .database import init_db, close_db
        await init_db()
    except Exception as e:
        logger.warning(f"Database init skipped: {e}")
    yield
    try:
        from .database import close_db
        await close_db()
    except Exception:
        pass


app = FastAPI(
    title="UAP NEXUS API",
    description="Unified Aerospace Phenomena tracking platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(incidents.router, prefix="/api/incidents", tags=["incidents"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(crawler.router, prefix="/api/crawler", tags=["crawler"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "UAP NEXUS",
        "version": "1.0.0",
        "docs": "/api/docs",
    }