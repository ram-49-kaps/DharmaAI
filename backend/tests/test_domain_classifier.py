import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.domain_classifier import classify_domain


def test_legal_query_routes_to_legal():
    decision = classify_domain("Explain Article 21 of the Constitution")
    assert decision.route == "legal"


def test_academic_document_routes_to_document_qa():
    message = """
Read this image

--- ATTACHMENT DETAILS ---
Attachment: certificate.png (Image Analysis JSON)
{
  "document_type": "certificate",
  "is_academic_or_legal_document": true,
  "summary": "Course completion certificate"
}
"""
    decision = classify_domain(message, has_attachment=True)
    assert decision.route == "academic_document"


def test_unrelated_query_routes_to_redirect():
    decision = classify_domain("Give me a recipe for pasta")
    assert decision.route == "unrelated"
