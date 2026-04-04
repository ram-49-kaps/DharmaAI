from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from services.llm import get_llm
from services.rag import retrieve_context
from services.knowledge_graph import get_knowledge_graph

PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     """You are a legal educator. Explain the case law using this structured format:

     **Facts:** (brief facts)
     **Issue:** (legal question before the court)
     **Judgment:** (what the court decided)
     **Principle:** (rule / ratio decidendi that came out of this case)
     **Significance:** (why it matters for Indian law)
     **IKS Connection:** (if applicable, connect to Dharma, Danda, or Puruṣārtha concepts —
      e.g., how the judgment upholds or reinterprets Dharmic duty, or how the sanction
      reflects Danda theory)

     Use the context below. Include citation. Do NOT give personal legal advice.

     Knowledge Graph Context:
     {kg_context}

     RAG Context:
     {context}"""),
    ("human", "{message}")
])


def run_caselaw_chain(message: str) -> str:
    context = retrieve_context(message)
    kg = get_knowledge_graph()
    kg_context = kg.enrich_context(message)
    chain   = PROMPT | get_llm() | StrOutputParser()
    return chain.invoke({
        "message": message,
        "context": context,
        "kg_context": kg_context or "No specific IKS graph connections found.",
    })
