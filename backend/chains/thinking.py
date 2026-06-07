import logging
import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from services.llm import get_fast_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a legal research assistant. The user has typed a query.
Generate exactly 3 progressive, logical, and professional action steps (written in present continuous tense, e.g., "Analyzing...", "Retrieving...") that a legal researcher would perform to answer this query.
Make the steps highly query-specific, using the key terms and context of the user's query.

Format your output as a raw JSON list of exactly 3 strings.
Example query: 'What is the punishment for murder?' -> ["Analyzing query for IPC and BNS murder provisions...", "Searching criminal case precedents on homicide...", "Synthesizing legal definitions and sentencing guidelines..."]

Do NOT include any markdown code blocks, do NOT write ```json, and do NOT write any text before or after the JSON list. Return ONLY the raw JSON list string."""

PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{query}")
])

def run_thinking_steps_chain(query: str) -> list[str]:
    """Generates 3 query-specific thinking steps in JSON format using the fast model."""
    try:
        llm = get_fast_llm()
        chain = PROMPT | llm | StrOutputParser()
        raw_output = chain.invoke({"query": query}).strip()
        
        # Clean up any potential markdown code blocks returned by LLM
        if raw_output.startswith("```"):
            lines = raw_output.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            raw_output = "\n".join(lines).strip()
            
        return json.loads(raw_output)
    except Exception as exc:
        logger.error(f"[Thinking] Chain failed: {exc}")
        # Return fallback generic steps in case of error
        return [
            "Analyzing legal query...",
            "Searching jurisprudential records...",
            "Preparing comprehensive synthesis..."
        ]
