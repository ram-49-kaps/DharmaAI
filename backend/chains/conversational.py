"""
Conversational chain handler for Prakarna AI v2.

Handles simple greetings and small talk without invoking the heavy RAG retrieval pipeline.
"""

import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from services.llm import invoke_with_fallback
from services.guardrails import SCOPE_GUARD

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = SCOPE_GUARD + """

You are Prakarna AI, an expert educational legal assistant specialising in Indian jurisprudence, constitutional law, and the Indian Knowledge System (IKS).

The user is currently just making small talk or greeting you. 
Respond in a friendly, conversational, and polite manner. 
Keep your response relatively brief. 
Always ask how you can help them with their legal research, case analysis, or learning today. 
Do NOT invent citations or pretend to do a legal analysis."""

PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{message}")
])

def run_conversational_chain(message: str, stream: bool = False, model_id: str = None):
    """
    Handle small talk and greetings quickly.
    Bypasses RAG retrieval to save time and tokens.
    """
    try:
        inputs = {"message": message}
        return invoke_with_fallback(
            lambda llm: PROMPT | llm | StrOutputParser(),
            inputs,
            stream=stream, model_id=model_id,
        )
    except Exception as exc:
        logger.error(f"[Conversational] Chain failed: {exc}")
        return "Hello! I am Prakarna AI. How can I assist you with your legal research or analysis today?"
