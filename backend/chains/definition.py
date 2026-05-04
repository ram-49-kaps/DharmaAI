"""Definition chain — explains legal terms from RAG sources."""

import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from services.llm import invoke_with_fallback
from services.rag_engine import get_rag_engine
from services.knowledge_graph import get_knowledge_graph

logger = logging.getLogger(__name__)

PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     """You are a legal educator specialising in Indian and comparative law.
     Use ONLY the provided sources to explain the legal term.

     Format:
     - Clear definition (2-3 sentences)
     - Etymology or origin if relevant (IKS or Latin/English)
     - Key elements or types
     - At least one cited example: [Source | Document | Section]
     - IKS connection if genuine (not forced)
     - Modern Indian law equivalent

     Do NOT use your training knowledge for the definition — use only the retrieved sources.
     If the term is not in the sources, say so explicitly.

     Knowledge Graph Context:
     {kg_context}

     Retrieved Sources:
     {context}"""),
    ("human", "Define and explain this legal term: {message}")
])


def run_definition_chain(message: str) -> str:
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
        logger.error(f"[Definition] Chain failed: {exc}")
        raise
