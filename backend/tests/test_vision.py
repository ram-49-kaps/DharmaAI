import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.vision import _coerce_analysis, _extract_json


def test_extract_json_from_wrapped_response():
    parsed = _extract_json('Here is JSON: {"document_type":"certificate","confidence":0.8}')
    assert parsed["document_type"] == "certificate"


def test_coerce_analysis_defaults_and_bounds_confidence():
    result = _coerce_analysis({
        "document_type": "certificate",
        "extracted_fields": "bad-shape",
        "confidence": 2,
        "is_academic_or_legal_document": True,
    })
    assert result["document_type"] == "certificate"
    assert result["extracted_fields"] == {}
    assert result["confidence"] == 1.0
    assert result["is_academic_or_legal_document"] is True
