from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from services.llm import get_llm
from services.rag import retrieve_context
from services.knowledge_graph import get_knowledge_graph

PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     """You are a legal educator specialising in Indian and comparative law.
     Use the context below to explain the legal term clearly.

     Rules:
     - Use bullet points
     - Keep it under 200 words
     - Include 1 example or citation
     - Mention Indian law sources where relevant (IKS, Dharmashastra, IPC, Constitution)
     - Where applicable, reference the Puruṣārtha framework (Dharma, Artha, Kama, Moksha)
       to show how the term fits within Indian philosophical jurisprudence
     - Do NOT give personal legal advice

     Knowledge Graph Context:
     {kg_context}

     RAG Context:
     {context}"""),
    ("human", "Define the legal term: {message}")
])


def run_definition_chain(message: str) -> str:
    context = retrieve_context(message)
    kg = get_knowledge_graph()
    kg_context = kg.enrich_context(message)
    chain   = PROMPT | get_llm() | StrOutputParser()
    return chain.invoke({
        "message": message,
        "context": context,
        "kg_context": kg_context or "No specific IKS graph connections found.",
    })
