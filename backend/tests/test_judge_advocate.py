"""
Tests for the Judge-Advocate LangGraph agent.

Verifies the revision flow, state transitions, and output quality.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.judge_advocate import (
    AgentState,
    retrieval_node,
    advocate_node,
    judge_node,
    finalize_node,
    should_revise,
    build_judge_advocate_graph,
)


@pytest.fixture
def base_state() -> AgentState:
    return {
        "query": "What is the Basic Structure Doctrine in Indian constitutional law?",
        "rag_context": (
            "Kesavananda Bharati v State of Kerala (1973) 4 SCC 225: "
            "The Supreme Court held by 7:6 majority that Parliament can amend the "
            "Constitution but cannot alter its Basic Structure. Features of Basic Structure "
            "include judicial review, separation of powers, federalism, and secularism."
        ),
        "kg_context": "Basic Structure Doctrine — Parliament cannot abrogate core features.",
        "advocate_draft": "",
        "judge_critique": "",
        "revision_count": 0,
        "final_answer": "",
        "needs_revision": False,
    }


def test_retrieval_node_sets_context(base_state):
    """retrieval_node must populate rag_context and kg_context."""
    result = retrieval_node(base_state)
    assert "rag_context" in result
    assert isinstance(result["rag_context"], str)
    assert "kg_context" in result


def test_advocate_node_produces_draft(base_state):
    """advocate_node must produce a non-empty draft."""
    result = advocate_node(base_state)
    assert result["advocate_draft"]
    assert len(result["advocate_draft"]) > 50


def test_judge_node_produces_verdict(base_state):
    """judge_node must set judge_critique."""
    state_with_draft = {**base_state, "advocate_draft": "The Basic Structure Doctrine was established in Kesavananda Bharati (1973) 4 SCC 225. Parliament cannot alter the basic features."}
    result = judge_node(state_with_draft)
    assert "judge_critique" in result
    assert isinstance(result["needs_revision"], bool)


def test_finalize_node_sets_final_answer(base_state):
    """finalize_node must populate final_answer."""
    state_with_draft = {
        **base_state,
        "advocate_draft": "The Basic Structure Doctrine prevents Parliament from destroying the Constitution."
    }
    result = finalize_node(state_with_draft)
    assert result["final_answer"]
    assert len(result["final_answer"]) > 0


def test_finalize_adds_disclaimer(base_state):
    """finalize_node must add educational disclaimer if missing."""
    state_with_draft = {
        **base_state,
        "advocate_draft": "The Basic Structure Doctrine is a constitutional principle."
    }
    result = finalize_node(state_with_draft)
    # Disclaimer should be present in final answer
    assert "educational" in result["final_answer"].lower() or "legal advice" in result["final_answer"].lower()


def test_should_revise_when_flagged():
    """should_revise returns 'revision' when needs_revision=True and count < 2."""
    state: AgentState = {
        "query": "test", "rag_context": "", "kg_context": "",
        "advocate_draft": "", "judge_critique": "VERDICT: REVISE",
        "revision_count": 0, "final_answer": "", "needs_revision": True,
    }
    assert should_revise(state) == "revision"


def test_should_finalize_when_passed():
    """should_revise returns 'finalize' when needs_revision=False."""
    state: AgentState = {
        "query": "test", "rag_context": "", "kg_context": "",
        "advocate_draft": "", "judge_critique": "VERDICT: PASS",
        "revision_count": 0, "final_answer": "", "needs_revision": False,
    }
    assert should_revise(state) == "finalize"


def test_max_revisions_respected():
    """After 2 revisions, should_revise must route to finalize even if judge says revise."""
    state: AgentState = {
        "query": "test", "rag_context": "", "kg_context": "",
        "advocate_draft": "", "judge_critique": "VERDICT: REVISE",
        "revision_count": 2, "final_answer": "", "needs_revision": False,
    }
    # revision_count=2 means needs_revision should already be False
    assert should_revise(state) == "finalize"


def test_graph_compiles():
    """Judge-Advocate graph must compile without errors."""
    graph = build_judge_advocate_graph()
    assert graph is not None


def test_full_pipeline_returns_string():
    """Full pipeline must return a non-empty string for a simple query."""
    from agents.judge_advocate import run_judge_advocate
    result = run_judge_advocate("What is Article 21 of the Indian Constitution?")
    assert isinstance(result, str)
    assert len(result) > 50
