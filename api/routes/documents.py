"""Documents API routes."""
import uuid

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class DocumentUpload(BaseModel):
    """Document upload request."""

    source_url: str
    incident_id: Optional[str] = None
    file_type: str = "PDF"


class DocumentResponse(BaseModel):
    """Document response."""

    id: str
    incident_id: Optional[str] = None
    source_url: str
    file_type: str
    ocr_text: str = ""
    uploaded_at: str = ""


# In-memory store
_documents: dict[str, dict] = {}


@router.get("")
async def list_documents(
    incident_id: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
):
    """List documents."""
    results = list(_documents.values())

    if incident_id:
        results = [d for d in results if d.get("incident_id") == incident_id]

    total = len(results)
    results = results[offset : offset + limit]

    return {"total": total, "documents": results}


@router.get("/{document_id}")
async def get_document(document_id: str):
    """Get document by ID."""
    if document_id not in _documents:
        raise HTTPException(status_code=404, detail="Document not found")

    return _documents[document_id]


@router.post("/upload")
async def upload_document(doc: DocumentUpload):
    """Upload/ingest new document."""
    import asyncio
    from datetime import datetime

    doc_id = str(uuid.uuid4())

    # Run OCR in background
    ocr_text = ""
    if doc.file_type.upper() == "PDF":
        try:
            from pipeline.ocr import simple_ocr

            result = await simple_ocr(doc.source_url)
            ocr_text = result.text
        except Exception as e:
            pass

    document = {
        "id": doc_id,
        "incident_id": doc.incident_id,
        "source_url": doc.source_url,
        "file_type": doc.file_type,
        "ocr_text": ocr_text,
        "uploaded_at": datetime.utcnow().isoformat(),
    }

    _documents[doc_id] = document

    return document


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete document."""
    if document_id not in _documents:
        raise HTTPException(status_code=404, detail="Document not found")

    del _documents[document_id]

    return {"deleted": True}