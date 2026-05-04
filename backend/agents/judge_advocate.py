"""
Judge-Advocate Agent — DharmaAI v2
────────────────────────────────────
LangGraph-based verification agent that ensures answer quality.

Flow: retrieval → advocate drafts → judge critiques → revise (≤2 times) → finalize

The judge checks:
1. Are citations present and accurate?
2. Is the IKS connection genuine or superficial?
3. Is the answer complete (not cut off)?
4. Does it actually answer the query?
"""

from __future__ import annotations

import logging
from typing import List, Optional, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from services.llm import get_llm
from services.rag_engine import get_rag_engine
from services.knowledge_graph import get_knowledge_graph

logger = logging.getLogger(__name__)


# ── State schema ──────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    query: str
    rag_context: str
    kg_context: str
    advocate_draft: str
    judge_critique: str
    revision_count: int
    final_answer: str
    needs_revision: bool


# ── Node functions ────────────────────────────────────────────────────────────

def retrieval_node(state: AgentState) -> AgentState:
    """Retrieve relevant sources from ChromaDB."""
    query = state["query"]
    try:
        engine = get_rag_engine()
        context, _ = engine.retrieve(query)
        kg = get_knowledge_graph()
        kg_context = kg.enrich_context(query, similarity_threshold=0.4)
        return {
            **state,
            "rag_context": context,
            "kg_context": kg_context or "No IKS connections found.",
        }
    except Exception as exc:
        logger.error(f"[JA] Retrieval failed: {exc}")
        return {
            **state,
            "rag_context": "Retrieval failed.",
            "kg_context": "",
        }


def advocate_node(state: AgentState) -> AgentState:
    """Draft an answer based on retrieved context."""
    llm = get_llm()

    system = """You are the Advocate in a Judge-Advocate review system.
Draft a comprehensive answer to the legal query using ONLY the provided sources.

Requirements:
- Answer the actual question asked
- Cite every legal claim: [IKS | source | section], [Statute | act | section], [Case | name | citation]
- Make IKS connections only where genuinely applicable
- Write a COMPLETE answer — do not stop mid-sentence
- Use clear structure with headers

Sources:
{rag_context}

Knowledge Graph:
{kg_context}""".format(
        rag_context=state["rag_context"],
        kg_context=state["kg_context"]
    )

    # If this is a revision, include the critique
    if state.get("judge_critique") and state.get("revision_count", 0) > 0:
        system += f"\n\nPREVIOUS CRITIQUE TO ADDRESS:\n{state['judge_critique']}"

    try:
        messages = [
            SystemMessage(content=system),
            HumanMessage(content=f"Query: {state['query']}"),
        ]
        response = llm.invoke(messages)
        draft = response.content if hasattr(response, "content") else str(response)
        return {**state, "advocate_draft": draft}
    except Exception as exc:
        logger.error(f"[JA] Advocate failed: {exc}")
        return {**state, "advocate_draft": f"Error generating response: {exc}"}


def judge_node(state: AgentState) -> AgentState:
    """
    Review the advocate's draft for quality.
    Returns critique and whether revision is needed.
    """
    llm = get_llm()

    system = """You are the Judge in a legal verification system. Review this draft answer.

Check:
1. CITATIONS: Does every legal claim have a citation? Are citations from the provided sources (not invented)?
2. IKS CONNECTIONS: Are IKS connections genuine and explained, or just superficial keyword mentions?
3. COMPLETENESS: Is the answer complete? Does it end mid-sentence?
4. RELEVANCE: Does the answer actually address the query asked?
5. ACCURACY: Do the cited sources actually say what the answer claims?

Available sources for verification:
{rag_context}

Respond in this exact format:
VERDICT: PASS or REVISE
ISSUES:
- [list issues if REVISE, or "None" if PASS]
CRITIQUE:
[2-3 sentences of specific feedback for the advocate, or "Answer meets all quality standards." if PASS]""".format(
        rag_context=state["rag_context"][:2000]  # Keep context manageable
    )

    try:
        messages = [
            SystemMessage(content=system),
            HumanMessage(
                content=f"Query: {state['query']}\n\nDraft Answer:\n{state['advocate_draft']}"
            ),
        ]
        response = llm.invoke(messages)
        critique_text = response.content if hasattr(response, "content") else str(response)

        needs_revision = (
            "VERDICT: REVISE" in critique_text
            and state.get("revision_count", 0) < 2
        )

        return {
            **state,
            "judge_critique": critique_text,
            "needs_revision": needs_revision,
        }
    except Exception as exc:
        logger.error(f"[JA] Judge failed: {exc}")
        return {**state, "judge_critique": "", "needs_revision": False}


def revision_node(state: AgentState) -> AgentState:
    """Increment revision count and route back to advocate."""
    return {**state, "revision_count": state.get("revision_count", 0) + 1}


def finalize_node(state: AgentState) -> AgentState:
    """Format the final answer with source summary."""
    draft = state.get("advocate_draft", "")

    # Add educational disclaimer if not present
    disclaimer = "\n\n---\n*This response is for educational purposes only and does not constitute legal advice.*"
    if "educational" not in draft.lower() and "legal advice" not in draft.lower():
        draft += disclaimer

    return {**state, "final_answer": draft}


# ── Conditional routing ───────────────────────────────────────────────────────

def should_revise(state: AgentState) -> str:
    """Route to revision or finalization based on judge verdict."""
    if state.get("needs_revision", False):
        return "revision"
    return "finalize"


# ── Graph construction ────────────────────────────────────────────────────────

def build_judge_advocate_graph() -> StateGraph:
    """Build and compile the Judge-Advocate LangGraph."""
    workflow = StateGraph(AgentState)

    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("advocate", advocate_node)
    workflow.add_node("judge", judge_node)
    workflow.add_node("revision", revision_node)
    workflow.add_node("finalize", finalize_node)

    workflow.set_entry_point("retrieval")
    workflow.add_edge("retrieval", "advocate")
    workflow.add_edge("advocate", "judge")
    workflow.add_conditional_edges(
        "judge",
        should_revise,
        {"revision": "revision", "finalize": "finalize"},
    )
    workflow.add_edge("revision", "advocate")
    workflow.add_edge("finalize", END)

    return workflow.compile()


# ── Public API ────────────────────────────────────────────────────────────────

_graph = None


def get_judge_advocate_graph():
    """Get singleton compiled graph."""
    global _graph
    if _graph is None:
        _graph = build_judge_advocate_graph()
    return _graph


def run_judge_advocate(query: str) -> str:
    """
    Run the full Judge-Advocate pipeline for a query.
    Returns the verified final answer.
    """
    graph = get_judge_advocate_graph()

    initial_state: AgentState = {
        "query": query,
        "rag_context": "",
        "kg_context": "",
        "advocate_draft": "",
        "judge_critique": "",
        "revision_count": 0,
        "final_answer": "",
        "needs_revision": False,
    }

    try:
        result = graph.invoke(initial_state)
        return result.get("final_answer", result.get("advocate_draft", ""))
    except Exception as exc:
        logger.error(f"[JA] Graph execution failed: {exc}")
        raise
