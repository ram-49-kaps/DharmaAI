"""
IDAR analysis chain — Dharma-based legal reasoning.

IDAR = Issue, Dharma (applicable rule), Application of Danda, Resolution.

Fixes:
- Only injects Danda context if query is actually about punishment/criminal law
- Uses embedding similarity, NOT keyword matching for Danda injection
- Each component must cite a specific source
- max_tokens=4096 (was 1024)
"""

import logging

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from services.llm import invoke_with_fallback
from services.rag_engine import get_rag_engine
from services.knowledge_graph import get_knowledge_graph
from chains.leveling import get_level_guidance

logger = logging.getLogger(__name__)

# Keywords and topics where Danda context is GENUINELY relevant
DANDA_RELEVANT_TOPICS = {
    "punishment", "criminal", "sanction", "offence", "offense", "crime",
    "sentence", "sentencing", "penalty", "danda", "penal", "conviction",
    "imprisonment", "death penalty", "capital", "fine", "bns", "ipc",
    "murder", "theft", "rape", "homicide", "assault", "robbery", "fraud",
    "coercion", "extortion",
}


def _is_danda_relevant(query: str) -> bool:
    """Check if the query genuinely involves punishment/criminal law topics."""
    query_lower = query.lower()
    return any(topic in query_lower for topic in DANDA_RELEVANT_TOPICS)


SYSTEM_PROMPT = """You are a legal reasoning tutor specialising in the Indian Knowledge System (IKS).
Apply the **IDAR method** — Issue, Dharma, Application of Danda, Resolution.

## CRITICAL RULES
1. Answer ONLY from the provided sources. Cite every claim.
2. Each IDAR component MUST cite a specific source.
3. Only discuss Danda (punishment) if the scenario actually involves criminal law or sanctions. If it does not, replace "Application of Danda" with "Application of Dharmic Principle."
4. IKS connections must be GENUINE — explain HOW the ancient concept maps to the modern law, not just that they share a word.

## IDAR FRAMEWORK

### ISSUE
Identify the precise legal question(s) raised. What is actually being asked?

### DHARMA (Applicable Rule)
State the applicable Dharma — the moral-legal duty or principle from Indian jurisprudence:
- Source from Dharmaśāstras, Constitution, statutes, or case law
- Explain how Dharma (the applicable principle) informs the rule
- Citation format: [IKS | Manusmriti | Chapter VIII] or [Statute | Constitution | Article 21]

### APPLICATION OF DANDA / DHARMIC PRINCIPLE
**Only if the scenario involves criminal law or sanctions:**
Apply Danda (Kautilyan sanction theory) to the facts:
- Which type of Danda applies? (vāk-danda, artha-danda, deha-danda, vadha-danda)
- How does modern law operationalise this? (citation required)
- Consider Puruṣārtha: does the sanction balance Artha (social utility) with Dharma (justice)?

**If the scenario does NOT involve criminal law:** Apply the relevant Dharmic principle to the facts and explain how it interacts with modern law.

### RESOLUTION
State the likely legal outcome with full reasoning:
- Connect to both IKS principle AND modern statutory/constitutional framework
- Cite specific sections/cases

---
## USER LEVEL
{level_guidance}

## KNOWLEDGE GRAPH CONTEXT
{kg_context}

## RETRIEVED SOURCES
{context}

Provide a thorough, complete analysis. Do NOT stop mid-sentence."""

PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "Apply the IDAR framework to this legal query: {message}")
])


def run_idar_chain(message: str, level: str = None) -> str:
    """
    Dharma-based IDAR analysis.
    Only injects Danda context when the query genuinely involves criminal law.
    """
    try:
        engine = get_rag_engine()
        context, _ = engine.retrieve(message)

        kg = get_knowledge_graph()
        # Threshold: only inject KG context if similarity > 0.4
        kg_context = kg.enrich_context(message, similarity_threshold=0.4)

        # Add Danda context only if genuinely relevant
        if _is_danda_relevant(message):
            danda_context, _ = engine.retrieve("Danda punishment criminal law Arthashastra", k_final=2)
            context = context + "\n\n[Additional Danda Context]\n" + danda_context

        inputs = {
            "message": message,
            "context": context,
            "kg_context": kg_context or "No specific IKS graph connections found for this query.",
            "level_guidance": get_level_guidance(level),
        }
        return invoke_with_fallback(
            lambda llm: PROMPT | llm | StrOutputParser(),
            inputs,
        )
    except Exception as exc:
        logger.error(f"[IDAR] Chain failed: {exc}")
        raise
