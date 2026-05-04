"""Statute chain — explains legislation from RAG sources."""

import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from services.llm import invoke_with_fallback
from services.rag_engine import get_rag_engine
from services.knowledge_graph import get_knowledge_graph

logger = logging.getLogger(__name__)

PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     """You are a legal educator specialising in Indian legislation and ancient Indian legal texts.
     Use ONLY the provided sources to explain the statute or provision.

     Format:
     **Full Name & Citation:** [from source]
     **Purpose:** (what problem it addresses)
     **Key Provisions:** (bullet list of sections from the retrieved source — cite each: [Statute | Act | Section X])
     **Application:** (how courts have applied it — cite cases from source)
     **IKS Connection:** (ONLY if genuine — how does this statute connect to IKS principles? Be specific.)

     IMPORTANT: Cite every provision. Do NOT use sections not in the source.
     If the statute is not in the sources, say so.

     Knowledge Graph Context:
     {kg_context}

     Retrieved Sources:
     {context}"""),
    ("human", "{message}")
])


def run_statute_chain(message: str) -> str:
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
        logger.error(f"[Statute] Chain failed: {exc}")
        raise
