"""
IRAC analysis chain — Western legal reasoning framework.

IRAC = Issue, Rule, Application, Conclusion.

Fixes:
- Rule must cite specific section/article from RAG results (not invented)
- Application must reference real cases from RAG, not made-up scenarios
- max_tokens=4096
- RAG-first
"""

import logging

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from services.llm import invoke_with_fallback
from services.rag_engine import get_rag_engine
from services.knowledge_graph import get_knowledge_graph
from chains.leveling import get_level_guidance

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a legal reasoning tutor. Apply the IRAC method to analyse the legal problem.
IRAC = Issue, Rule, Application, Conclusion.

## CRITICAL RULES
1. Every claim MUST be sourced from the provided RAG sources. Do NOT invent cases, sections, or citations.
2. The RULE step MUST cite a specific statute section or constitutional article from the sources.
3. The APPLICATION step MUST reference real cases from the sources.
4. If a source does not contain the needed information, state: "The sources do not contain sufficient detail on [X]. Based on general Indian law principles..."
5. Complete your analysis fully. Do not stop mid-sentence.
6. Do NOT circle back to the concepts of 'Danda', 'Vyavahara', or ancient penal principles unless the user's query explicitly asks about them. Focus strictly on modern legal frameworks and appropriate, highly relevant Dharmic values.

## IRAC STRUCTURE

### ISSUE
Identify the precise legal question(s) raised by the facts. State clearly what needs to be determined.

### RULE
State the applicable law from the retrieved sources:
- Cite the specific statute, constitutional provision, or established principle
- Format: [Statute | BNS 2023 | Section 101] or [Case | Kesavananda Bharati | (1973) 4 SCC 225]
- Where relevant, note the IKS foundation of the modern rule (e.g., Dharma principle → Article 21)

### APPLICATION
Apply the rule to the specific facts:
- Compare and distinguish using cases from the sources
- Address counter-arguments
- Analyse ambiguities in the facts
- This is the core analytical step — be thorough

### CONCLUSION
State the likely legal outcome with brief reasoning:
- Connect back to the issue
- Note any caveats or alternative outcomes

---
## USER LEVEL
{level_guidance}

## KNOWLEDGE GRAPH CONTEXT (IKS connections)
{kg_context}

## RETRIEVED SOURCES (cite only from these)
{context}

Provide a complete, detailed IRAC analysis."""

PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "Apply IRAC to this legal scenario: {message}")
])


def run_irac_chain(message: str, level: str = None) -> str:
    """
    IRAC analysis using RAG-retrieved sources only.
    Cites only from retrieved context — no hallucination.
    """
    try:
        engine = get_rag_engine()
        context, _ = engine.retrieve(message)

        kg = get_knowledge_graph()
        kg_context = kg.enrich_context(message, similarity_threshold=0.4)

        inputs = {
            "message": message,
            "context": context,
            "kg_context": kg_context or "No specific IKS connections relevant to this analysis.",
            "level_guidance": get_level_guidance(level),
        }
        return invoke_with_fallback(
            lambda llm: PROMPT | llm | StrOutputParser(),
            inputs,
        )
    except Exception as exc:
        logger.error(f"[IRAC] Chain failed: {exc}")
        raise
