"""
Tests for intent router.

Critical requirement: must NOT default to irac_analysis for normal queries.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from chains.router import detect_intent


# ── General queries must NOT become irac_analysis ────────────────────────────

GENERAL_QA_CASES = [
    "What is mens rea?",
    "How does contract law work in India?",
    "What are fundamental rights in India?",
    "Tell me about Indian criminal law",
    "What is the role of the Supreme Court?",
    "How does PIL work?",
    "What is consideration in contract law?",
    "Explain the Indian legal system",
    "What is Dharma in Indian jurisprudence?",
    "What is Danda?",
]

EXPLICIT_IRAC_CASES = [
    "Apply IRAC to this scenario: A sold B a car with hidden defects",
    "Do an IRAC analysis of this contract dispute",
    "IRAC analysis of negligence case",
    "Analyse using IRAC: the tenant damaged the property",
]

EXPLICIT_IDAR_CASES = [
    "Apply IDAR to this criminal case",
    "Use the Dharma framework to analyse this dispute",
    "IKS-based analysis of this situation",
    "Use IDAR for this scenario",
]

DEFINITION_CASES = [
    "What is habeas corpus?",
    "Define actus reus",
    "What does mens rea mean?",
    "Explain the concept of stare decisis",
]

CASE_LOOKUP_CASES = [
    "Tell me about Kesavananda Bharati case",
    "What was decided in Maneka Gandhi?",
    "Explain the Vishaka judgment",
    "What happened in Puttaswamy case?",
]


@pytest.mark.parametrize("query", GENERAL_QA_CASES)
def test_general_queries_not_irac(query):
    """General legal questions must NOT be classified as irac_analysis."""
    intent = detect_intent(query)
    assert intent != "irac_analysis", (
        f"Query '{query}' was wrongly classified as irac_analysis. Got: {intent}"
    )
    assert intent != "idar_analysis", (
        f"Query '{query}' was wrongly classified as idar_analysis. Got: {intent}"
    )


@pytest.mark.parametrize("query", EXPLICIT_IRAC_CASES)
def test_explicit_irac_classified_correctly(query):
    """Queries with explicit 'IRAC' or 'apply IRAC' must be classified as irac_analysis."""
    intent = detect_intent(query)
    assert intent == "irac_analysis", (
        f"Query '{query}' should be irac_analysis but got: {intent}"
    )


@pytest.mark.parametrize("query", EXPLICIT_IDAR_CASES)
def test_explicit_idar_classified_correctly(query):
    """Queries with explicit IDAR/Dharma framework request must be idar_analysis."""
    intent = detect_intent(query)
    assert intent == "idar_analysis", (
        f"Query '{query}' should be idar_analysis but got: {intent}"
    )


@pytest.mark.parametrize("query", DEFINITION_CASES)
def test_definition_queries(query):
    """Definition queries should be classified as 'definition'."""
    intent = detect_intent(query)
    assert intent == "definition", (
        f"Query '{query}' should be definition but got: {intent}"
    )


@pytest.mark.parametrize("query", CASE_LOOKUP_CASES)
def test_case_lookup_queries(query):
    """Case lookup queries should be classified as 'case_lookup'."""
    intent = detect_intent(query)
    assert intent == "case_lookup", (
        f"Query '{query}' should be case_lookup but got: {intent}"
    )


def test_unknown_returns_general_qa():
    """Completely unrecognised input must default to general_qa."""
    intent = detect_intent("xyzkdfahsdfhakshdf legal?")
    assert intent == "general_qa"


def test_danda_query_not_idar():
    """A query about Danda should NOT auto-trigger idar_analysis."""
    intent = detect_intent("What is Danda in Arthashastra?")
    assert intent != "idar_analysis", (
        "Query about Danda should not auto-trigger IDAR. "
        "IDAR must only trigger when user explicitly requests it."
    )
