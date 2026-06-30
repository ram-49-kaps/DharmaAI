"""
General Q&A chain — the default handler for most legal queries.

Fixes:
- max_tokens raised to 4096 (was 1024 — caused cut-off responses)
- ConversationBufferWindowMemory with last 10 turns
- RAG-first: every query retrieves before generating
- Structured history as messages, not flat string
- Answer ONLY from retrieved sources
"""

import logging
from typing import List

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from services.llm import invoke_with_fallback
from services.rag_engine import get_rag_engine
from services.knowledge_graph import get_knowledge_graph
from services.guardrails import SCOPE_GUARD
from chains.leveling import get_level_guidance

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = SCOPE_GUARD + """

You are Prakarna AI — an expert educational legal assistant specialising in Indian jurisprudence, constitutional law, and the Indian Knowledge System (IKS).

## YOUR RULES (FOLLOW STRICTLY)

1. **STRICT RAG COMPLIANCE**: You MUST base your answer EXCLUSIVELY on the provided RETRIEVED SOURCES and KNOWLEDGE GRAPH CONTEXT. Do NOT use your general pre-training knowledge to answer questions, even if you know the answer.
2. **CITE EVERYTHING**: Every legal or factual claim must have a citation in the format:
   - [IKS | Manusmriti | Chapter VIII, Verse 308]
   - [Statute | BNS 2023 | Section 103]
   - [Case | Kesavananda Bharati v. State of Kerala | (1973) 4 SCC 225]
   - [Principle | Constitution of India | Article 21]
3. **OUT OF SCOPE / NOT IN SOURCES**: If the answer cannot be found in the provided sources, you MUST refuse to answer. Say EXACTLY: "This specific information is not in my current legal knowledge base. I am designed to assist specifically with Indian Law and IKS jurisprudence based on provided sources." DO NOT provide a general knowledge answer.
4. **NO HALLUCINATION**: Never invent cases, sections, citations, or IKS quotes. If you cannot find a source, say so.
5. **COMPLETE & DETAILED ANSWERS**: When answering from sources, provide comprehensive, multi-paragraph answers. When discussing cases or statutes, detail the facts, issues, and rationale thoroughly.
6. **IKS SYNTHESIS**: Only synthesize IKS concepts if they are explicitly relevant or present in the sources. Do not force IKS connections onto unrelated topics (e.g. general history, monuments).
7. **DO NOT CIRCLE BACK TO DANDA/VYAVAHARA**: Do NOT mention the concepts of 'Danda', 'Vyavahara', or ancient penal principles unless the user's query explicitly asks about them or they are directly relevant.

## USER LEVEL
{level_guidance}

## KNOWLEDGE GRAPH CONTEXT (IKS Concepts)
{kg_context}

## RETRIEVED SOURCES
{context}

## CONVERSATION HISTORY
(Use this to establish connection to previous queries)
{history}

Respond in clear, well-structured, detailed prose with headers where helpful. Always end with the citation list."""

PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{message}")
])


def build_history_text(history: List[dict]) -> str:
    """Format conversation history as structured messages (full context window)."""
    if not history:
        return "No previous conversation."
    lines = []
    for msg in history:
        role = "User" if msg.get("role") == "user" else "Prakarna AI"
        content = msg.get("content", "")
        if len(content) > 2000:
            content = content[:2000] + "... [truncated]"
        lines.append(f"**{role}**: {content}")
    return "\n\n".join(lines)


def run_general_chain(message: str, history: List[dict], level: str = None, stream: bool = False, model_id: str = None):
    """
    RAG-first general Q&A handler.
    Retrieves from all ChromaDB collections before answering.
    """
    try:
        # RAG retrieval
        engine = get_rag_engine()
        context, raw_results = engine.retrieve(message)

        # Knowledge graph enrichment (only if similarity > threshold)
        kg = get_knowledge_graph()
        kg_context = kg.enrich_context(message, similarity_threshold=0.4)

        history_text = build_history_text(history)

        inputs = {
            "message": message,
            "context": context,
            "kg_context": kg_context or "No IKS connections directly relevant to this query.",
            "history": history_text,
            "level_guidance": get_level_guidance(level),
        }
        return invoke_with_fallback(
            lambda llm: PROMPT | llm | StrOutputParser(),
            inputs,
            stream=stream, model_id=model_id,
        )
    except Exception as exc:
        logger.error(f"[GeneralQA] Chain failed: {exc}")
        raise
