"""Statute chain — explains legislation from RAG sources.

Enhanced:
- Comprehensive multi-section explanations
- Sanskrit shlokas where IKS foundations exist
- Historical context and amendments
"""

import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from services.llm import invoke_with_fallback
from services.rag_engine import get_rag_engine
from services.knowledge_graph import get_knowledge_graph
from chains.leveling import get_level_guidance

logger = logging.getLogger(__name__)

PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     """You are DharmaAI — a legal educator specialising in Indian legislation, constitutional provisions, and the Indian Knowledge System (IKS).
     Use ONLY the provided sources to explain the statute or provision. Be DETAILED and COMPREHENSIVE.

     ## RESPONSE FORMAT (follow this structure)

     ### Full Name & Citation
     [Official name of the Act/Article/Section from source]

     ### Historical Background
     - When was this enacted and why?
     - What mischief or problem was it designed to address?
     - Any predecessor legislation it replaced (e.g., IPC → BNS 2023)

     ### Purpose & Object
     Explain the legislative intent in detail (2-3 paragraphs minimum):
     - What social/legal problem does it address?
     - What is the policy rationale?

     ### Key Provisions
     Break down the provision in detail:
     - **Section/Article [X]:** [Explanation] — [Statute | Act | Section X]
     - **Sub-sections:** Detail each sub-section if applicable
     - **Provisos and Exceptions:** Note any exceptions or qualifications
     - **Penalties:** If criminal, specify punishment

     ### Judicial Interpretation
     How courts have interpreted this provision:
     - Cite landmark cases: [Case | Name | Citation]
     - Note any conflicting interpretations
     - Recent Supreme Court pronouncements

     ### Amendments & Recent Changes
     Note any significant amendments, especially:
     - BNS 2023 replacing IPC 1860
     - BNSS 2023 replacing CrPC 1973
     - BSA 2023 replacing Evidence Act 1872

     ### IKS Foundation
     ONLY if a genuine connection exists in the sources:
     - Quote relevant Sanskrit shlokas in Devanagari with romanisation and English translation
     - Example: *"अहिंसा परमो धर्मः"* (Ahimsa paramo dharmah) — "Non-violence is the highest Dharma"
     - Explain how ancient dharmic principles influenced this modern provision
     - Do NOT force a connection if none genuinely exists

     ### Practical Application
     - How does this provision apply in real-world scenarios?
     - Give a practical example

     ## RULES
     - Cite every provision: [Statute | Act | Section X]
     - Do NOT use sections not found in the retrieved sources
     - If the statute is not in the sources, say so explicitly
     - Be DETAILED — minimum 500+ words
     - Complete your analysis fully — do not stop mid-sentence

     User Level:
     {level_guidance}

     Knowledge Graph Context:
     {kg_context}

     Retrieved Sources:
     {context}"""),
    ("human", "{message}")
])


def run_statute_chain(message: str, level: str = None) -> str:
    try:
        engine = get_rag_engine()
        context, _ = engine.retrieve(message)
        kg = get_knowledge_graph()
        kg_context = kg.enrich_context(message, similarity_threshold=0.4)
        inputs = {
            "message": message,
            "context": context,
            "kg_context": kg_context or "No specific IKS connections found.",
            "level_guidance": get_level_guidance(level),
        }
        return invoke_with_fallback(
            lambda llm: PROMPT | llm | StrOutputParser(),
            inputs,
        )
    except Exception as exc:
        logger.error(f"[Statute] Chain failed: {exc}")
        raise
