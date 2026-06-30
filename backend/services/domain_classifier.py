"""Hybrid domain classifier for Prakarna AI chat routing.

Architecture:
  1. Fast keyword pre-filter (instant, handles ~85% of queries)
  2. Lightweight LLM fallback via Groq 8B (~200ms, handles ~15% ambiguous queries)

Design principles:
  - Enum-based route names for type safety
  - Configurable confidence threshold via env var
  - LRU cache for repeated ambiguous queries
  - Structured JSON from LLM classifier
  - Graceful fallback: LLM failure → keyword decision
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from services.guardrails import (
    contains_medical_content,
    contains_non_legal_content,
    IMAGE_REJECTION_MESSAGE,
    GENERAL_REJECTION_MESSAGE,
)

logger = logging.getLogger(__name__)


# ── Route Enum ────────────────────────────────────────────────────────────────

class Route(str, Enum):
    """All valid domain routes. Inherits str for JSON serialisability."""
    LEGAL = "legal"
    ACADEMIC_DOCUMENT = "academic_document"
    CONVERSATION = "conversation"
    UNRELATED = "unrelated"


# ── Decision dataclass ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class DomainDecision:
    route: Route
    confidence: float  # 0.0 – 1.0
    reason: str
    source: str  # "keyword" | "llm" | "fallback"


# ── Configurable threshold ────────────────────────────────────────────────────

CONFIDENCE_THRESHOLD = float(os.getenv("DOMAIN_CLASSIFIER_THRESHOLD", "0.7"))


# ── Keyword sets ──────────────────────────────────────────────────────────────

LEGAL_KEYWORDS = {
    # Core legal
    "law", "legal", "case", "judgment", "judgement", "court", "supreme court",
    "high court", "constitution", "article", "section", "act", "statute",
    "ipc", "bns", "crpc", "bnss", "evidence", "contract", "tort", "crime",
    "criminal", "civil", "petition", "writ", "pil", "rights", "liability",
    "precedent", "mens rea", "actus reus", "habeas corpus", "bail", "fir",
    "trial", "verdict", "prosecution", "defendant", "plaintiff", "advocate",
    "lawyer", "judge", "bench", "tribunal", "arbitration", "mediation",
    "regulation", "ordinance", "amendment", "penalty", "offense", "offence",
    "convicted", "acquitted", "sentence", "imprisonment", "fine", "appeal",
    "review", "quash", "stay order", "injunction", "decree", "summon",
    "chargesheet", "cognizable", "non-cognizable", "bailable", "non-bailable",
    "remand", "parole", "probation", "extradition",

    # Indian Knowledge System / Dharma
    "dharma", "iks", "ikrs", "irac", "filac", "idar", "jurisprudence",
    "arthashastra", "manusmriti", "nyaya", "danda", "rajadharma",
    "vyavahara", "smriti", "shruti", "vedic", "kautilya", "chanakya",
    "dharmashastra", "dharmasutra", "indian knowledge system",
    "ancient indian", "vedic law", "hindu law", "muslim law",
    "personal law", "customary law",
}

ACADEMIC_KEYWORDS = {
    "certificate", "course", "university", "college", "school", "student",
    "academic", "education", "degree", "diploma", "transcript", "marksheet",
    "assignment", "project", "resume", "cv", "internship", "workshop",
    "datacamp", "coursera", "udemy", "edx", "grade", "learning", "study",
}

CONVERSATION_EXACT = {
    "hello", "hi", "hey", "good morning", "good afternoon", "good evening",
    "namaste", "pranam", "who are you", "what can you do",
    "how are you", "thank you", "thanks", "bye", "goodbye",
}

CLEARLY_UNRELATED_PATTERNS = [
    r"\b(recipe|cook|bake|ingredient|calories|nutrition)\b",
    r"\b(weather|forecast|temperature|humidity|rain today)\b",
    r"\b(score|cricket|football|hockey|ipl|match|wicket|goal)\b",
    r"\b(movie|bollywood|hollywood|song|lyrics|music|album|actor|actress)\b",
    r"\b(stock market|nifty|sensex|bitcoin|crypto|trading|forex)\b",
    r"\b(game|gaming|minecraft|fortnite|pubg|valorant)\b",
    r"\b(workout|gym|exercise|diet plan|weight loss|yoga pose)\b",
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _contains_any(text: str, keywords: set[str]) -> bool:
    return any(kw in text for kw in keywords)


def _matches_unrelated_pattern(text: str) -> bool:
    return any(re.search(p, text) for p in CLEARLY_UNRELATED_PATTERNS)


# ── Step 1: Keyword pre-filter ────────────────────────────────────────────────

def _keyword_classify(message: str, has_attachment: bool = False) -> DomainDecision:
    """Fast rule-based classifier. Returns high confidence for clear matches,
    low confidence (0.0) when uncertain — triggering the LLM fallback."""
    text = (message or "").lower()

    # Explicit document flags from attachment OCR
    if "is_academic_or_legal_document" in text and "true" in text:
        if _contains_any(text, ACADEMIC_KEYWORDS):
            return DomainDecision(Route.ACADEMIC_DOCUMENT, 0.95, "Attachment flagged as academic.", "keyword")
        if _contains_any(text.replace("is_academic_or_legal_document", ""), LEGAL_KEYWORDS):
            return DomainDecision(Route.LEGAL, 0.95, "Attachment flagged as legal.", "keyword")
        return DomainDecision(Route.ACADEMIC_DOCUMENT, 0.90, "Attachment present; defaulting to academic.", "keyword")

    # Attachments with academic context
    if has_attachment and _contains_any(text, ACADEMIC_KEYWORDS):
        return DomainDecision(Route.ACADEMIC_DOCUMENT, 0.95, "Attachment with academic keywords.", "keyword")

    # Legal / IKS signal
    if _contains_any(text, LEGAL_KEYWORDS):
        return DomainDecision(Route.LEGAL, 0.95, "Legal/IKS keywords detected.", "keyword")

    # Academic signal
    if _contains_any(text, ACADEMIC_KEYWORDS):
        return DomainDecision(Route.ACADEMIC_DOCUMENT, 0.95, "Academic keywords detected.", "keyword")

    # Exact small-talk match
    clean = re.sub(r"\s+", " ", text).strip(" ?!.")
    if clean in CONVERSATION_EXACT:
        return DomainDecision(Route.CONVERSATION, 0.99, "Exact small-talk match.", "keyword")

    # Attachment without clear keywords → check for non-legal content first
    if has_attachment:
        if contains_medical_content(text):
            return DomainDecision(Route.UNRELATED, 0.95, "Attachment contains medical/non-legal content.", "keyword")
        if contains_non_legal_content(text):
            return DomainDecision(Route.UNRELATED, 0.90, "Attachment contains non-legal content.", "keyword")
        return DomainDecision(Route.LEGAL, 0.80, "Attachment present; no specific keywords.", "keyword")

    # Obviously off-topic
    if _matches_unrelated_pattern(text):
        return DomainDecision(Route.UNRELATED, 0.90, "Matched off-topic pattern.", "keyword")

    # UNCERTAIN — no signal at all
    return DomainDecision(Route.LEGAL, 0.0, "No keyword signal; uncertain.", "keyword")


# ── Step 2: LLM domain classifier ────────────────────────────────────────────

_LLM_DOMAIN_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     """You are a domain classifier for Prakarna AI, a legal education chatbot.
Classify the user query into exactly ONE domain. Respond with ONLY valid JSON.

Domains:
- "legal" — Anything about law, jurisprudence, Indian Knowledge System (IKS/IKRS), legal concepts, rights, constitutions, statutes, cases, Dharma, Arthashastra, or legal education
- "academic_document" — Queries about academic certificates, coursework, study material, university documents
- "conversation" — Greetings, small talk, questions about the chatbot itself (e.g. "who are you", "which model are you using")
- "unrelated" — Clearly off-topic queries (cooking, weather, sports, entertainment, stocks, gaming)

IMPORTANT: When in doubt, classify as "legal". Prakarna AI can handle a wide range of queries about Indian law and IKS.

Respond with ONLY this JSON format, no other text:
{"route": "<domain>", "reason": "<brief reason>"}"""),
    ("human", "{message}")
])


@lru_cache(maxsize=128)
def _llm_classify_cached(message: str) -> tuple[str, str]:
    """Cached LLM domain classification. Returns (route, reason).
    Cache key is the exact message string; LRU evicts least-recently-used."""
    from services.llm import invoke_fast

    raw = invoke_fast(
        lambda llm: _LLM_DOMAIN_PROMPT | llm | StrOutputParser(),
        {"message": message},
    )

    # Parse structured JSON response
    cleaned = raw.strip()
    # Handle markdown code fences if the LLM wraps the response
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    parsed = json.loads(cleaned)
    route = parsed.get("route", "legal")
    reason = parsed.get("reason", "LLM classification")
    return (route, reason)


def _llm_classify(message: str, keyword_decision: DomainDecision) -> DomainDecision:
    """LLM fallback classifier. On any failure, returns the keyword decision."""
    try:
        route_str, reason = _llm_classify_cached(message)

        # Validate route against enum
        try:
            route = Route(route_str)
        except ValueError:
            logger.warning(f"[DomainClassifier] LLM returned invalid route '{route_str}'; falling back to keyword decision")
            return DomainDecision(keyword_decision.route, 0.5, keyword_decision.reason, "fallback")

        # Assign confidence based on the routing path (not LLM-invented)
        llm_confidence = 0.85  # LLM decisions get a fixed high confidence
        return DomainDecision(route, llm_confidence, f"LLM: {reason}", "llm")

    except json.JSONDecodeError as e:
        logger.warning(f"[DomainClassifier] LLM returned invalid JSON: {e}; falling back to keyword decision")
        return DomainDecision(keyword_decision.route, 0.5, keyword_decision.reason, "fallback")
    except Exception as e:
        logger.warning(f"[DomainClassifier] LLM classifier failed: {e}; falling back to keyword decision")
        return DomainDecision(keyword_decision.route, 0.5, keyword_decision.reason, "fallback")


# ── Public API ────────────────────────────────────────────────────────────────

def classify_domain(message: str, has_attachment: bool = False) -> DomainDecision:
    """Hybrid domain classifier: fast keyword pre-filter + LLM fallback.

    1. Run keyword classifier (instant)
    2. If confidence >= threshold → return immediately (fast path)
    3. If confidence < threshold → call LLM classifier (~200ms)
    4. On LLM failure → fall back to keyword decision
    """
    keyword_decision = _keyword_classify(message, has_attachment)

    if keyword_decision.confidence >= CONFIDENCE_THRESHOLD:
        logger.debug(f"[DomainClassifier] Keyword fast-path: {keyword_decision.route.value} "
                      f"(confidence={keyword_decision.confidence:.2f})")
        return keyword_decision

    # Ambiguous — call lightweight LLM
    logger.info(f"[DomainClassifier] Keyword uncertain (confidence={keyword_decision.confidence:.2f}); "
                f"invoking LLM fallback for: '{message[:80]}...'")
    llm_decision = _llm_classify(message, keyword_decision)
    logger.info(f"[DomainClassifier] LLM decision: {llm_decision.route.value} "
                f"(confidence={llm_decision.confidence:.2f}, source={llm_decision.source})")
    return llm_decision


def friendly_redirect(message: str) -> str:
    """Friendly scope-rejection message for clearly off-topic queries."""
    lower = (message or "").lower()
    # Use image-specific rejection for medical/visual content
    if contains_medical_content(lower) or "--- ATTACHMENT DETAILS ---" in message:
        return IMAGE_REJECTION_MESSAGE
    return GENERAL_REJECTION_MESSAGE
