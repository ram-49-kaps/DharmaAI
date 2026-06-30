"""Response-depth guidance shared by Prakarna AI chains."""

from typing import Optional


LEVEL_GUIDANCE = {
    "beginner": (
        "Audience level: Beginner. Explain legal ideas in plain language, define jargon, "
        "use short examples, and keep the structure easy to follow while still citing sources."
    ),
    "intermediate": (
        "Audience level: Intermediate law student. Include doctrine, statutory structure, "
        "important exceptions, and case reasoning with moderate depth."
    ),
    "advanced": (
        "Audience level: Advanced student or researcher. Provide deeper doctrinal analysis, "
        "competing interpretations, policy rationale, and careful source-based caveats."
    ),
    "practitioner": (
        "Audience level: Practitioner. Be precise, practice-oriented, and detailed. Emphasise "
        "legal tests, litigation risk, procedural posture, authorities, exceptions, and next steps."
    ),
}


def get_level_guidance(level: Optional[str]) -> str:
    """Return prompt guidance for the requested user level."""
    normalized = (level or "beginner").strip().lower()
    if normalized == "academician":
        normalized = "advanced"
    return LEVEL_GUIDANCE.get(normalized, LEVEL_GUIDANCE["beginner"])
