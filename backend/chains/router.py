"""
Intent router for DharmaAI v2.

DEFAULT intent is general_qa — NOT legal_reasoning.
Only routes to irac_analysis or idar_analysis when user EXPLICITLY requests it.

Fixes:
- Bug: was defaulting to legal_reasoning (IRAC) for normal questions
- Bug: was not distinguishing follow-up queries from new queries
"""

import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from services.llm import invoke_with_fallback

logger = logging.getLogger(__name__)

INTENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     """You are a legal query intent classifier. Classify the user's query into EXACTLY ONE intent label.

INTENT DEFINITIONS AND EXAMPLES:

1. "definition" — User asks what a legal term means.
   Examples:
   - "What is mens rea?"
   - "Define actus reus"
   - "What does habeas corpus mean?"
   - "Explain the concept of Dharma in law"
   - "What is Danda?"
   - "What is consideration in contract law?"

2. "case_lookup" — User asks about a specific court case or judgment.
   Examples:
   - "Tell me about Kesavananda Bharati case"
   - "What was decided in Maneka Gandhi?"
   - "Explain the Vishaka judgment"
   - "What is the Puttaswamy case about?"
   - "What happened in Olga Tellis case?"

3. "statute_lookup" — User asks about a specific law, act, section, or code.
   Examples:
   - "What does Section 300 IPC say?"
   - "Explain Article 21 of the Constitution"
   - "What are the provisions of the Contract Act?"
   - "What is Section 63 of BNS 2023?"
   - "What does Article 32 provide?"

4. "irac_analysis" — User EXPLICITLY requests IRAC analysis. ONLY classify as this if the user says one of these exact phrases:
   - "apply IRAC", "do an IRAC", "IRAC analysis", "analyse using IRAC", "IRAC breakdown", "use IRAC framework"
   Examples:
   - "Apply IRAC to this contract dispute scenario"
   - "Do an IRAC analysis of this negligence case"
   - "Give me an IRAC breakdown of this constitutional problem"

5. "idar_analysis" — User EXPLICITLY requests IDAR/Dharma framework. ONLY classify as this if the user says one of these exact phrases:
   - "apply IDAR", "use IDAR", "Dharma framework", "IKS analysis", "IKS-based analysis", "use Dharmic framework", "Dharma-based analysis"
   Examples:
   - "Apply IDAR to this criminal case"
   - "Use the Dharma framework to analyse this dispute"
   - "IKS-based analysis of this situation"

6. "comparative" — User asks to compare two legal concepts, cases, or systems.
   Examples:
   - "Compare IRAC and IDAR"
   - "How does BNS 2023 differ from IPC 1860?"
   - "Compare Article 19 and Article 21"
   - "What is the difference between Dharma and modern law?"
   - "Compare Arthashastra and the Indian Contract Act"

7. "follow_up" — User continues a previous conversation or asks for more detail.
   Examples:
   - "Continue"
   - "Tell me more"
   - "Explain that further"
   - "What about the punishment aspect?"
   - "Can you elaborate on the IDAR part?"
   - "Give more details"
   - "What else?"

8. "general_qa" — EVERYTHING ELSE. This is the DEFAULT for any legal question that doesn't fit above.
   Examples:
   - "How does the criminal justice system work in India?"
   - "What are my rights if arrested?"
   - "How does contract law apply to online agreements?"
   - "What is the punishment for murder in India?"
   - "How is the Indian Constitution structured?"
   - "What is the role of the Supreme Court?"
   - "How does the PIL mechanism work?"

CRITICAL RULES:
- Default to "general_qa" for any normal legal question, even if it asks to "explain" something or solve a problem.
- NEVER classify a question as "irac_analysis" unless the user EXPLICITLY types the word "IRAC".
- NEVER classify as "idar_analysis" unless the user EXPLICITLY types the word "IDAR" or "Dharma framework".
- Questions about Danda, Dharma, or IKS are just "definition" or "general_qa", NOT "idar_analysis".
- Reply with ONLY the intent label. No punctuation. No explanation. No quotes."""),
    ("human", "{message}")
])


def detect_intent(message: str) -> str:
    """
    Detect the intent of a legal query.
    Defaults to 'general_qa' for any unrecognised or ambiguous input.
    """
    try:
        result = invoke_with_fallback(
            lambda llm: INTENT_PROMPT | llm | StrOutputParser(),
            {"message": message},
        ).strip().lower()

        valid = {
            "definition", "case_lookup", "statute_lookup",
            "irac_analysis", "idar_analysis", "comparative",
            "follow_up", "general_qa",
        }

        # Legacy label mapping for backwards compatibility
        legacy_map = {
            "legal_reasoning": "irac_analysis",
            "idar": "idar_analysis",
            "case_law": "case_lookup",
            "statute": "statute_lookup",
            "general": "general_qa",
        }

        if result in valid:
            return result
        if result in legacy_map:
            return legacy_map[result]

        logger.warning(f"[Router] Unknown intent '{result}' — defaulting to general_qa")
        return "general_qa"

    except Exception as exc:
        logger.error(f"[Router] Intent detection failed: {exc} — defaulting to general_qa")
        return "general_qa"
