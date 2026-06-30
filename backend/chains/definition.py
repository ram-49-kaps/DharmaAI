"""Definition chain — explains legal terms from RAG sources.

Enhanced:
- Longer, more comprehensive explanations
- Sanskrit shlokas with translations when IKS sources contain them
- Level-based depth adaptation
"""

import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from services.llm import invoke_with_fallback
from services.rag_engine import get_rag_engine
from services.knowledge_graph import get_knowledge_graph
from chains.leveling import get_level_guidance
from services.guardrails import SCOPE_GUARD

logger = logging.getLogger(__name__)

PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     SCOPE_GUARD + """\n\nYou are Prakarna AI — a legal educator specialising in Indian law, constitutional law, and the Indian Knowledge System (IKS).
     Use ONLY the provided sources to explain the legal term. Be DETAILED and COMPREHENSIVE.

     ## RESPONSE FORMAT (follow this structure)

     ### Definition
     Provide a thorough definition (4-6 sentences minimum). Explain the term clearly with its scope, applicability, and legal significance.

     ### Etymology & Origin
     - Trace the term's origin (Sanskrit/Latin/English/Hindi as applicable)
     - If an IKS/Sanskrit term exists, provide the original shloka in Devanagari with romanisation and English translation
     - Format: *"धर्मो रक्षति रक्षितः"* (Dharmo rakshati rakshitah) — "Dharma protects those who protect Dharma" — Manusmriti VIII.15

     ### Key Elements & Classification
     - Break down the term into its constituent elements
     - List different types, categories, or variations if applicable
     - Provide sub-definitions where relevant

     ### Legal Provisions & Case Law
     - Cite specific statute sections: [Statute | Act Name | Section X]
     - Reference landmark cases: [Case | Name | Citation]
     - Explain how courts have interpreted this term

     ### IKS Foundation
     - ONLY if a genuine connection exists in the sources
     - Quote relevant Sanskrit shlokas with translation
     - Explain the conceptual bridge between ancient IKS and modern law
     - Do NOT force a connection if none exists

     ### Practical Application
     - Give a real-world example of how this term applies
     - Note any recent developments or amendments

     ## RULES
     - Do NOT use your training knowledge — use ONLY the retrieved sources
     - If the term is not in the sources, say so explicitly
     - Be DETAILED. A complete answer should be 500+ words minimum
     - Cite every claim: [Source | Document | Section/Verse]

     User Level:
     {level_guidance}

     Knowledge Graph Context:
     {kg_context}

     Retrieved Sources:
     {context}"""),
    ("human", "Define and explain this legal term comprehensively: {message}")
])


def run_definition_chain(message: str, level: str = None, stream: bool = False, model_id: str = None):
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
            stream=stream, model_id=model_id,
        )
    except Exception as exc:
        logger.error(f"[Definition] Chain failed: {exc}")
        raise
