"""
Tests for RAG engine retrieval quality.
Verifies ChromaDB collections, hybrid search, and context building.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.rag_engine import RAGEngine, COLLECTIONS


@pytest.fixture(scope="module")
def engine():
    return RAGEngine()


def test_engine_initialises(engine):
    """RAG engine must initialise without error."""
    engine._ensure_init()
    assert engine._client is not None


def test_all_collections_exist(engine):
    """All 4 collections must exist after initialisation."""
    engine._ensure_init()
    for name in COLLECTIONS:
        assert name in engine._collections, f"Collection '{name}' missing"


def test_add_and_retrieve(engine):
    """Documents added to a collection must be retrievable."""
    test_doc = "Kesavananda Bharati case established the Basic Structure Doctrine in 1973."
    engine.add_documents(
        documents=[test_doc],
        metadatas=[{"title": "Test Case", "citation": "(1973) 4 SCC 225", "source_type": "Case", "category": "case_law", "section": "", "page": ""}],
        ids=["test_kesavananda_001"],
        collection_name="case_law",
    )
    results = engine.hybrid_search("Kesavananda Basic Structure", k=5)
    assert len(results) > 0
    contents = [r["content"] for r in results]
    assert any("Kesavananda" in c or "Basic Structure" in c for c in contents)


def test_hybrid_search_returns_scores(engine):
    """Search results must include similarity scores."""
    results = engine.hybrid_search("constitutional law India", k=5)
    for r in results:
        assert "score" in r
        assert "content" in r
        assert "metadata" in r
        assert "collection" in r


def test_rerank_reduces_results(engine):
    """Rerank must return at most k results."""
    results = engine.hybrid_search("contract law consideration", k=10)
    if results:
        reranked = engine.rerank(results, "contract law consideration", k=3)
        assert len(reranked) <= 3


def test_build_context_has_source_tags(engine):
    """Built context must include source citation tags."""
    results = engine.hybrid_search("Article 21 right to life", k=3)
    if results:
        context = engine.build_context(results)
        assert "[Source:" in context


def test_retrieve_returns_tuple(engine):
    """retrieve() must return (context_string, list_of_results)."""
    context, results = engine.retrieve("what is mens rea")
    assert isinstance(context, str)
    assert isinstance(results, list)
    assert len(context) > 0


def test_retrieve_not_found_graceful(engine):
    """retrieve() must handle no results gracefully."""
    context, results = engine.retrieve("xyzabcnonexistentquery12345")
    assert isinstance(context, str)


def test_collection_count(engine):
    """collection_count must return a non-negative integer."""
    count = engine.collection_count("case_law")
    assert isinstance(count, int)
    assert count >= 0
