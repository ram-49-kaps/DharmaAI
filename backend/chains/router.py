from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from services.llm import get_llm

INTENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     """You are a legal query classifier. Classify the user's legal question into EXACTLY ONE of:
     - definition       (asking what a legal term means)
     - case_law         (asking about a court case or judgment)
     - statute          (asking about a law, act, section, or code)
     - legal_reasoning  (asking to apply IRAC or analyse a scenario using Western framework)
     - idar             (asking to apply IDAR, Dharma-based analysis, or analyse using Indian Knowledge System / IKS / Dharmashastra / Danda / Purushartha)
     - general          (anything else legal)

     Reply with ONLY the intent label. No punctuation, no explanation."""),
    ("human", "{message}")
])


def detect_intent(message: str) -> str:
    chain  = INTENT_PROMPT | get_llm() | StrOutputParser()
    result = chain.invoke({"message": message}).strip().lower()
    valid  = {"definition", "case_law", "statute", "legal_reasoning", "idar", "general"}
    return result if result in valid else "general"
