from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from services.llm import get_llm
from services.rag import retrieve_context
from services.knowledge_graph import get_knowledge_graph

PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     """You are a legal reasoning tutor. Apply the IRAC method to analyse the legal problem:

     **ISSUE:** Identify the precise legal question(s) raised.

     **RULE:** State the applicable law — statute, constitutional provision, or case law precedent. Include citations.

     **APPLICATION:** Apply the rule to the specific facts. Compare and distinguish. This is the core analytical step.

     **CONCLUSION:** State the likely legal outcome with reasoning.

     ---
     Guidelines:
     - Reference Indian law (IPC, Constitution, Contract Act, case law) where applicable
     - Where relevant, connect with Dharma-based reasoning from Indian jurisprudence
     - Consider the Puruṣārtha framework when evaluating ethical dimensions:
       * Dharma (duty/righteousness) — is the outcome just?
       * Artha (social utility) — does it serve the public interest?
       * Kama (individual interest) — are legitimate desires protected?
       * Moksha (ultimate resolution) — does it achieve legal closure?
     - Be educational, not advisory
     - Include at least one citation

     Knowledge Graph Context:
     {kg_context}

     RAG Context:
     {context}"""),
    ("human", "Apply IRAC to this legal scenario: {message}")
])


def run_irac_chain(message: str) -> str:
    context = retrieve_context(message)
    kg = get_knowledge_graph()
    kg_context = kg.enrich_context(message)
    chain   = PROMPT | get_llm() | StrOutputParser()
    return chain.invoke({
        "message": message,
        "context": context,
        "kg_context": kg_context or "No specific IKS graph connections found.",
    })
