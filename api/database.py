"""Database connection and models."""
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from sqlalchemy import Column, String, Text, Date, DateTime, Boolean, JSON, Float, ForeignKey, Enum as SQLEnum, text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import DeclarativeBase, relationship
import uuid

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


@dataclass
class IncidentDB(Base):
    """Incident database model."""

    __tablename__ = "incidents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String(20), nullable=False, index=True)
    agency = Column(String(100), default="")
    incident_date = Column(Date, nullable=True)
    release_date = Column(Date, nullable=True)
    location_name = Column(String(255), default="")
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    incident_type = Column(String(100), default="")
    craft_description = Column(Text, default="")
    witnesses = Column(JSON, default=list)
    resolution = Column(String(20), default="UNKNOWN")
    raw_doc_url = Column(String(500), default="")
    extracted_text = Column(Text, default="")
    embedding = Column(ARRAY(Float), nullable=True)
    is_new = Column(Boolean, default=True)
    foia_matches = Column(ARRAY(UUID), default=list)
    image_ids = Column(ARRAY(UUID), default=list)
    tags = Column(ARRAY(String), default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


@dataclass
class DocumentDB(Base):
    """Document database model."""

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=True)
    source_url = Column(String(500), nullable=False)
    file_type = Column(String(20), default="")
    file_path = Column(String(500), nullable=True)
    ocr_text = Column(Text, default="")
    uploaded_at = Column(DateTime, default=datetime.utcnow)


# Database connection
_engine: Optional[AsyncEngine] = None
_session_factory: Optional[sessionmaker] = None


async def get_engine() -> AsyncEngine:
    """Get database engine."""
    global _engine

    if _engine is None:
        database_url = os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@localhost:5432/uapnexus",
        )
        _engine = create_async_engine(database_url, echo=False)
        logger.info(f"Database engine created: {database_url.split('@')[1] if '@' in database_url else database_url}")

    return _engine


async def get_session() -> AsyncSession:
    """Get database session."""
    engine = await get_engine()
    async with AsyncSession(engine) as session:
        yield session


async def init_db():
    """Initialize database tables."""
    try:
        engine = await get_engine()

        async with engine.begin() as conn:
            # Enable pgvector extension
            try:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            except Exception:
                pass

            # Create tables
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Database initialized")
    except Exception as e:
        logger.warning(f"Database init skipped: {e}")


async def close_db():
    """Close database connection."""
    global _engine

    if _engine:
        await _engine.dispose()
        _engine = None

    logger.info("Database connection closed")