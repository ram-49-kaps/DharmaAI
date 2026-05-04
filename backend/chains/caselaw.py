"""Case law chain — explains court judgments from RAG sources."""

import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from services.llm import invoke_with_fallback
from services.rag_engine import get_rag_engine
from services.knowledge_graph import get_knowledge_graph

logger = logging.getLogger(__name__)

PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     """You are a legal educator. Explain the case using ONLY the provided sources.

     Format:
     **Citation:** [full citation from source]
     **Facts:** (brief, accurate facts from source)
     **Issue:** (exact legal question from source)
     **Judgment / Holding:** (what the court decided)
     **Ratio Decidendi:** (binding principle established)
     **Significance:** (why it matters for Indian law)
     **IKS Connection:** (ONLY if a genuine connection exists — explain HOW it connects)

     IMPORTANT: Do NOT invent facts, citations, or holdings. Use only the retrieved sources.
     If the case is not in the sources, say: "This case is not in my current knowledge base.
     Please consult official law reports."

     Knowledge Graph Context:
     {kg_context}

     Retrieved Sources:
     {context}"""),
    ("human", "{message}")
])


def run_caselaw_chain(message: str) -> str:
    try:
        engine = get_rag_engine()
        context, _ = engine.retrieve(message)
        kg = get_knowledge_graph()
        kg_context = kg.enrich_context(message, similarity_threshold=0.4)
        inputs = {
            "message": message,
            "context": context,
            "kg_context": kg_context or "No specific IKS connections found.",
        }
        return invoke_with_fallback(
            lambda llm: PROMPT | llm | StrOutputParser(),
            inputs,
        )
    except Exception as exc:
        logger.error(f"[Caselaw] Chain failed: {exc}")
        raise
