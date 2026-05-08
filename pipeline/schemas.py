"""Pydantic schemas for pipeline data."""
from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Source(str, Enum):
    """Incident source."""

    PURSUE = "PURSUE"
    AARO = "AARO"
    FOIA = "FOIA"
    CIVILIAN = "CIVILIAN"


class Resolution(str, Enum):
    """Incident resolution status."""

    UNRESOLVED = "UNRESOLVED"
    RESOLVED = "RESOLVED"
    PENDING = "PENDING"
    UNKNOWN = "UNKNOWN"


class IncidentSchema(BaseModel):
    """Full incident schema."""

    id: Optional[str] = None
    source: Source
    agency: str = ""
    incident_date: Optional[date] = None
    release_date: Optional[date] = None
    location_name: str = ""
    lat: Optional[float] = None
    lon: Optional[float] = None
    incident_type: str = ""
    craft_description: str = ""
    witnesses: list[dict] = Field(default_factory=list)
    resolution: Resolution = Resolution.UNKNOWN
    raw_doc_url: str = ""
    extracted_text: str = ""
    embedding: Optional[list[float]] = None
    is_new: bool = True
    foia_matches: list[str] = Field(default_factory=list)
    image_ids: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DocumentSchema(BaseModel):
    """Document schema."""

    id: Optional[str] = None
    incident_id: Optional[str] = None
    source_url: str = ""
    file_type: str = ""
    file_path: Optional[str] = None
    ocr_text: str = ""
    uploaded_at: Optional[datetime] = None


class AlertSubscriptionSchema(BaseModel):
    """Alert subscription."""

    id: Optional[str] = None
    channel_type: str  # "telegram", "discord", "email"
    channel_id: str  # chat_id, webhook, email
    filters: dict = Field(default_factory=dict)  # source, agency, etc
    created_at: Optional[datetime] = None