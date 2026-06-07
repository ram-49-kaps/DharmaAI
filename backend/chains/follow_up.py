"""
Follow-up chain — handles continuation queries.

Detects continuation requests ("continue", "explain more", "what about X")
and uses the last 3 message pairs + their RAG sources for context continuity.
"""

import logging
from typing import List

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from services.llm import invoke_with_fallback
from services.rag_engine import get_rag_engine
from services.knowledge_graph import get_knowledge_graph
from chains.leveling import get_level_guidance

logger = logging.getLogger(__name__)

FOLLOW_UP_INDICATORS = {
    "continue", "tell me more", "explain more", "elaborate", "expand",
    "go on", "what else", "more detail", "in more depth", "further",
    "what about", "how about", "and what", "also tell", "additionally",
    "can you explain", "please explain", "clarify", "i want to know more",
}


def is_follow_up(message: str) -> bool:
    """Quick check if message is a continuation query."""
    msg_lower = message.lower().strip()
    return any(indicator in msg_lower for indicator in FOLLOW_UP_INDICATORS)


SYSTEM_PROMPT = """You are DharmaAI, continuing a legal consultation.

The user is asking a follow-up question or requesting elaboration on the previous exchange.

## PREVIOUS CONVERSATION (last 3 exchanges)
{history}

## FOLLOW-UP CONTEXT FROM KNOWLEDGE BASE
{context}

## KNOWLEDGE GRAPH CONTEXT
{kg_context}

## YOUR TASK
Provide a detailed, complete response to the follow-up.
- Maintain topic continuity with the previous conversation
- Retrieve and cite new relevant information from the sources above
- Do not repeat what was already covered — expand and deepen the analysis
- Cite every new claim: [IKS | source | section] or [Case | name | citation] or [Statute | act | section]
- If the follow-up introduces a new sub-topic, address it specifically
- Do NOT stop mid-sentence. Write a complete response.
- Do NOT circle back to the concepts of 'Danda', 'Vyavahara', or ancient penal principles unless the user's query explicitly asks about them. Focus strictly on modern law and relevant IKS/Dharma connections.

## USER LEVEL
{level_guidance}"""

PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{message}")
])


def run_follow_up_chain(message: str, history: List[dict], level: str = None) -> str:
    """
    Handles follow-up/continuation queries with topic continuity.
    Uses last 3 exchanges + retrieval for context.
    """
    try:
        # Build recent history context
        recent = history
        history_parts = []
        for msg in recent:
            role = "User" if msg.get("role") == "user" else "DharmaAI"
            content = msg.get("content", "")[:2000]
            history_parts.append(f"**{role}**: {content}")
        history_text = "\n\n".join(history_parts) if history_parts else "No previous conversation."

        # Extract topic from last assistant message for retrieval
        last_assistant = next(
            (m.get("content", "") for m in reversed(recent) if m.get("role") == "assistant"),
            ""
        )
        retrieval_query = f"{message} {last_assistant[:500]}" if last_assistant else message

        engine = get_rag_engine()
        context, _ = engine.retrieve(retrieval_query)

        kg = get_knowledge_graph()
        kg_context = kg.enrich_context(retrieval_query, similarity_threshold=0.4)

        inputs = {
            "message": message,
            "context": context,
            "kg_context": kg_context or "No additional IKS connections found.",
            "history": history_text,
            "level_guidance": get_level_guidance(level),
        }
        return invoke_with_fallback(
            lambda llm: PROMPT | llm | StrOutputParser(),
            inputs,
        )
    except Exception as exc:
        logger.error(f"[FollowUp] Chain failed: {exc}")
        raise


def generate_suggested_questions(user_query: str, assistant_answer: str) -> str:
    """Generate 2 relevant follow-up questions the user might ask next based on the response."""
    try:
        from services.llm import get_fast_llm
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser

        prompt = ChatPromptTemplate.from_messages([
            ("system", 
             "You are a friendly, warm legal research companion. Based on the user's original query and the assistant's response, "
             "generate exactly 2 relevant, high-quality, professional follow-up questions the user might want to ask next. "
             "Format them as bullet points starting with '- '. Underneath the questions, write a short, warm, and friendly "
             "concluding sentence inviting the user to proceed with one of these questions if they would like, or ask another query of their choice."),
            ("human", "User Query: {query}\n\nAssistant Response: {response}")
        ])

        llm = get_fast_llm()
        chain = prompt | llm | StrOutputParser()
        result = chain.invoke({"query": user_query, "response": assistant_answer})
        return result.strip()
    except Exception as exc:
        logger.error(f"[FollowUp] Failed to generate suggested questions: {exc}")
        return ""
