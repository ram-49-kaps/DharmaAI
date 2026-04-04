from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from services.llm import get_llm
from services.rag import retrieve_context
from services.knowledge_graph import get_knowledge_graph
from typing import List

PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     """You are DharmaAI — an educational legal assistant for Indian law students, grounded in both
     modern Indian law and the Indian Knowledge System (IKS).

     Answer the question using the context below. Format your response with:
     - Clear bullet points or numbered steps
     - At least one citation (case name + citation, or statute section)
     - A brief note on Indian jurisprudential perspective where relevant, considering:
       * Dharma (the applicable moral-legal principle)
       * Danda (how sanctions/enforcement apply)
       * Puruṣārtha (how the four aims — Dharma, Artha, Kama, Moksha — contextualise the issue)
     - End with: "📚 This is for educational purposes only, not legal advice."

     Conversation so far:
     {history}

     Knowledge Graph Context:
     {kg_context}

     Relevant RAG context:
     {context}"""),
    ("human", "{message}")
])


def build_history_text(history: List[dict]) -> str:
    if not history:
        return "None"
    lines = []
    for msg in history[-6:]:   # keep last 3 exchanges
        role = "User" if msg.get("role") == "user" else "Assistant"
        lines.append(f"{role}: {msg.get('content', '')}")
    return "\n".join(lines)


def run_general_chain(message: str, history: List[dict]) -> str:
    context      = retrieve_context(message)
    kg = get_knowledge_graph()
    kg_context = kg.enrich_context(message)
    history_text = build_history_text(history)
    chain        = PROMPT | get_llm() | StrOutputParser()
    return chain.invoke({
        "message": message,
        "context": context,
        "kg_context": kg_context or "No specific IKS graph connections found.",
        "history": history_text,
    })
