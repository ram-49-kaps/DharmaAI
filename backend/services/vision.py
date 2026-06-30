"""Gemini Vision image analysis with OCR fallback for Prakarna AI."""

from __future__ import annotations

import io
import json
import logging
import os
import re
from typing import Any

logger = logging.getLogger(__name__)

VISION_MODEL = os.getenv("GEMINI_VISION_MODEL", "gemini-2.5-flash")
VISION_MODEL_FALLBACKS = [
    model.strip()
    for model in os.getenv(
        "GEMINI_VISION_MODEL_FALLBACKS",
        "gemini-2.5-flash,gemini-2.0-flash,gemini-1.5-flash-latest",
    ).split(",")
    if model.strip()
]


DEFAULT_ANALYSIS = {
    "document_type": "unknown",
    "extracted_fields": {},
    "summary": "",
    "confidence": 0.0,
    "is_academic_or_legal_document": False,
    "suggested_query_context": "",
}


def _coerce_analysis(data: dict[str, Any]) -> dict[str, Any]:
    result = dict(DEFAULT_ANALYSIS)
    result.update({k: v for k, v in data.items() if k in result})
    if not isinstance(result["extracted_fields"], dict):
        result["extracted_fields"] = {}
    try:
        result["confidence"] = max(0.0, min(1.0, float(result["confidence"])))
    except (TypeError, ValueError):
        result["confidence"] = 0.0
    result["is_academic_or_legal_document"] = bool(result["is_academic_or_legal_document"])
    return result


def _extract_json(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text or "")
        if not match:
            raise
        return json.loads(match.group(0))


def _ocr_image(content: bytes) -> str:
    from PIL import Image
    import pytesseract

    tesseract_paths = [
        "/opt/homebrew/bin/tesseract",
        "/usr/local/bin/tesseract",
        "/usr/bin/tesseract",
    ]
    for path in tesseract_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            break

    image = Image.open(io.BytesIO(content))
    return (pytesseract.image_to_string(image) or "").strip()


def _fallback_from_ocr(content: bytes, filename: str) -> dict[str, Any]:
    try:
        text = _ocr_image(content)
    except Exception as exc:
        logger.warning("[Vision] OCR fallback failed: %s", exc)
        text = ""
    lower = text.lower()
    is_academic = any(word in lower for word in ["certificate", "course", "student", "university", "college", "grade", "completed"])
    is_legal = any(word in lower for word in ["court", "case", "section", "article", "law", "legal", "constitution"])
    summary = text[:700] if text else "No readable text could be extracted from this image."
    return _coerce_analysis({
        "document_type": "image_ocr_fallback",
        "extracted_fields": {"filename": filename, "ocr_text": text},
        "summary": summary,
        "confidence": 0.45 if text else 0.1,
        "is_academic_or_legal_document": is_academic or is_legal,
        "suggested_query_context": "Answer only from OCR text; extraction confidence is limited.",
    })


def analyze_image(content: bytes, filename: str, content_type: str, user_prompt: str = "") -> dict[str, Any]:
    """Return structured image analysis from Gemini Vision, falling back to OCR."""
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)
            prompt = f"""
Analyze this uploaded image for Prakarna AI.
Return ONLY valid JSON with exactly these keys:
document_type, extracted_fields, summary, confidence, is_academic_or_legal_document, suggested_query_context.

Rules:
- document_type: short label such as certificate, marksheet, legal_notice, contract, court_order, screenshot, unknown.
- extracted_fields: object of visible important fields.
- summary: concise factual description grounded only in the image.
- confidence: number from 0 to 1.
- is_academic_or_legal_document: true only for academic, study, legal, legal-career, or certificate material.
- suggested_query_context: one sentence describing how Prakarna AI should answer.

User prompt: {user_prompt or "No prompt provided."}
Filename: {filename}
"""
            last_error = None
            models_to_try = list(dict.fromkeys([VISION_MODEL, *VISION_MODEL_FALLBACKS]))
            for model_name in models_to_try:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=[
                            types.Part.from_bytes(data=content, mime_type=content_type or "image/png"),
                            prompt,
                        ],
                    )
                    analysis = _coerce_analysis(_extract_json(response.text or ""))
                    analysis["provider"] = "gemini_vision"
                    analysis["model"] = model_name
                    return analysis
                except Exception as exc:
                    last_error = exc
                    logger.warning("[Vision] Gemini Vision model %s failed: %s", model_name, exc)
            if last_error:
                raise last_error
        except Exception as exc:
            logger.warning("[Vision] Gemini Vision failed, using OCR fallback: %s", exc)

    analysis = _fallback_from_ocr(content, filename)
    analysis["provider"] = "ocr_fallback"
    return analysis
