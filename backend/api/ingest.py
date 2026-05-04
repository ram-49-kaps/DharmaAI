"""
PDF ingestion endpoint — admin only.

POST /api/ingest
  - Accepts: PDF file + category
  - Returns: chunks_created, collection, filename
"""

import logging
import tempfile
import os
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from auth.firebase_auth import get_admin_user
from models.schemas import IngestResponse
from services.pdf_ingestion import PDFIngestor

logger = logging.getLogger(__name__)
router = APIRouter()

VALID_CATEGORIES = {"iks_texts", "modern_law", "case_law"}


@router.post("/api/ingest", response_model=IngestResponse)
async def ingest_pdf(
    file: UploadFile = File(...),
    category: str = Form(...),
    _user: dict = Depends(get_admin_user),
):
    """
    Ingest a PDF into the specified ChromaDB collection.
    Requires admin Firebase UID.
    """
    if category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category '{category}'. Must be one of: {sorted(VALID_CATEGORIES)}",
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    content = await file.read()
    if len(content) > 50 * 1024 * 1024:  # 50 MB limit
        raise HTTPException(status_code=413, detail="File too large (max 50 MB)")

    # Save to temp file and ingest
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        ingestor = PDFIngestor()
        chunks_count = ingestor.ingest(tmp_path, category)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.error(f"[Ingest] Error ingesting {file.filename}: {exc}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}")
    finally:
        os.unlink(tmp_path)

    return IngestResponse(
        status="success",
        chunks_created=chunks_count,
        collection=category,
        filename=file.filename,
    )
