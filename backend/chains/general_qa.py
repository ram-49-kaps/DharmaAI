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

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are DharmaAI — an expert educational legal assistant specialising in Indian jurisprudence, constitutional law, and the Indian Knowledge System (IKS).

## YOUR RULES (FOLLOW STRICTLY)

1. **RAG-FIRST**: Answer ONLY from the provided sources. Do NOT use your general training knowledge to answer legal questions.
2. **CITE EVERYTHING**: Every legal claim must have a citation in the format:
   - [IKS | Manusmriti | Chapter VIII, Verse 308]
   - [Statute | BNS 2023 | Section 103]
   - [Case | Kesavananda Bharati v. State of Kerala | (1973) 4 SCC 225]
   - [Principle | Constitution of India | Article 21]
3. **IF NOT IN SOURCES**: If the sources do not contain information to answer the question, say: "This specific information is not in my current knowledge base. I can tell you that [brief general context from sources if any]. For detailed information, please consult the original text."
4. **NO HALLUCINATION**: Never invent cases, sections, or citations. If you cannot find a source, say so.
5. **COMPLETE & DETAILED ANSWERS**: Do not be brief. Provide comprehensive, multi-paragraph answers. When discussing cases or statutes, detail the facts, issues, and rationale thoroughly. Do not stop mid-sentence.
6. **IKS SYNTHESIS**: Do not just append IKS quotes. Deeply synthesize how the ancient IKS concepts (like Dharma) conceptually form the foundation for the modern legal provisions discussed. Establish a strong, meaningful connection.
7. **AVOID DANDA OVERUSE**: Do not overuse the term 'Danda'. Only use it when specifically discussing penal consequences or when it is heavily featured in the retrieved text.

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
    """Format conversation history as structured messages (last 10 turns)."""
    if not history:
        return "No previous conversation."
    lines = []
    for msg in history[-10:]:
        role = "User" if msg.get("role") == "user" else "DharmaAI"
        content = msg.get("content", "")
        if len(content) > 2000:
            content = content[:2000] + "... [truncated]"
        lines.append(f"**{role}**: {content}")
    return "\n\n".join(lines)


def run_general_chain(message: str, history: List[dict]) -> str:
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
        }
        return invoke_with_fallback(
            lambda llm: PROMPT | llm | StrOutputParser(),
            inputs,
        )
    except Exception as exc:
        logger.error(f"[GeneralQA] Chain failed: {exc}")
        raise
