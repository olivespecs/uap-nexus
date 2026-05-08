"""Incidents API routes."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from pipeline.schemas import IncidentSchema, Source, Resolution

router = APIRouter()


# In-memory store for MVP (replace with Postgres)
_incidents: dict[str, dict] = {}


@router.get("")
async def list_incidents(
    source: Optional[str] = Query(None, description="Filter by source"),
    agency: Optional[str] = Query(None, description="Filter by agency"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
):
    """List incidents with optional filters."""
    results = list(_incidents.values())

    if source:
        results = [i for i in results if i["source"] == source]

    if agency:
        results = [i for i in results if agency.lower() in i.get("agency", "").lower()]

    total = len(results)
    results = results[offset : offset + limit]

    return {"total": total, "incidents": results}


@router.get("/{incident_id}")
async def get_incident(incident_id: str):
    """Get single incident by ID."""
    if incident_id not in _incidents:
        raise HTTPException(status_code=404, detail="Incident not found")

    return _incidents[incident_id]


@router.post("")
async def create_incident(incident: IncidentSchema):
    """Create new incident."""
    import uuid

    incident_id = str(uuid.uuid4())
    incident_dict = incident.model_dump()
    incident_dict["id"] = incident_id
    incident_dict["created_at"] = incident.updated_at.isoformat()

    _incidents[incident_id] = incident_dict

    return {"id": incident_id, **incident_dict}


@router.get("/search")
async def search_incidents(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, le=50),
):
    """Semantic search (placeholder for pgvector)."""
    # TODO: Implement actual vector search
    results = []

    for incident in _incidents.values():
        text = f"{incident.get('craft_description', '')} {incident.get('location_name', '')}"
        if q.lower() in text.lower():
            results.append(incident)
            if len(results) >= limit:
                break

    return {"results": results}


@router.put("/{incident_id}")
async def update_incident(incident_id: str, incident: IncidentSchema):
    """Update incident."""
    if incident_id not in _incidents:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident_dict = incident.model_dump()
    _incidents[incident_id].update(incident_dict)

    return _incidents[incident_id]


@router.delete("/{incident_id}")
async def delete_incident(incident_id: str):
    """Delete incident."""
    if incident_id not in _incidents:
        raise HTTPException(status_code=404, detail="Incident not found")

    del _incidents[incident_id]

    return {"deleted": True}