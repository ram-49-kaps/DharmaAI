from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from services.llm import get_llm
from services.rag import retrieve_context
from services.knowledge_graph import get_knowledge_graph

PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     """You are a legal educator specialising in Indian legislation and ancient Indian legal texts.
     Explain the statute or legal provision in this format:

     **Full Name & Citation:**
     **Purpose:** (what problem it addresses)
     **Key Provisions:** (bullet list of important sections)
     **Application:** (how it is used in practice)
     **Related Cases / IKS Connection:** (link to case law or Indian Knowledge System where applicable.
      Consider connections to Dharmaśāstra precedents, Arthashastra provisions, or how the
      statute operationalises Dharmic principles through modern Danda)

     Use the context provided. Do NOT give personal legal advice.

     Knowledge Graph Context:
     {kg_context}

     RAG Context:
     {context}"""),
    ("human", "{message}")
])


def run_statute_chain(message: str) -> str:
    context = retrieve_context(message)
    kg = get_knowledge_graph()
    kg_context = kg.enrich_context(message)
    chain   = PROMPT | get_llm() | StrOutputParser()
    return chain.invoke({
        "message": message,
        "context": context,
        "kg_context": kg_context or "No specific IKS graph connections found.",
    })
