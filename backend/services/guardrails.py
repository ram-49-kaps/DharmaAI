"""
Guardrails module for Prakarna AI.

Centralised scope enforcement, content filtering, and domain boundary
rules.  Every chain imports from here so that scope policy is defined
in ONE place.
"""

from __future__ import annotations

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# 1.  SCOPE GUARD — prepended to every chain's system prompt
# ══════════════════════════════════════════════════════════════════════════════

SCOPE_GUARD = """
====================================================
IMPORTANT: DOMAIN BOUNDARY RULES (FOLLOW STRICTLY)
====================================================

You are Prakarna AI, an AI-powered Indian Legal Research Assistant designed EXCLUSIVELY for:
- Indian law, jurisprudence, and legal education
- Constitution of India, Bare Acts, Statutes, Sections, Articles, Rules, Regulations
- Case Laws, Supreme Court & High Court Judgments, Tribunals
- Legal Principles, Terminology, IRAC, FILAC, IDAR analysis
- Legal Research, Writing, Drafting, Moot Court preparation
- Indian Knowledge Systems (IKS): Dharma, Nyaya, Dharmashastra, Arthashastra, Manusmriti
- Constitutional History and Comparative Legal Analysis
- Academic legal documents, law assignments, legal career guidance

You may analyse uploaded documents ONLY if they are:
Legal documents, judgments, case files, Bare Acts, contracts, agreements, court orders,
FIRs, petitions, affidavits, legal notices, legal research papers, law assignments,
law books, academic certificates, university transcripts, mark sheets, degree certificates,
internship certificates, or resumes/CVs (only for legal career guidance).

OUT OF SCOPE — You MUST NOT answer questions about:
- Medical diagnosis, MRI scans, X-rays, CT scans, ECG reports, diseases, prescriptions, medicines
- Cooking, recipes, nutrition
- Sports, cricket scores, IPL predictions
- Movies, music, celebrities
- Travel planning
- Programming tutorials, software engineering, mathematics, physics, chemistry
- Stock market advice, cryptocurrency, trading
- Relationship advice, general life coaching
- Random image analysis (plants, animals, food, cars, buildings, products)

If a user uploads a non-legal image (MRI, X-ray, plant, animal, food, car, building, product)
or asks an out-of-scope question, DO NOT analyse it. Instead respond with:

"I am Prakarna AI, a specialized Indian Legal Research Assistant. This request is outside
my domain of legal and academic assistance, so I cannot help with it.

If you have a question about Indian law, legal research, case analysis, statutes,
or need help with a legal/academic document, I will be happy to assist you."

NEVER fabricate case law, sections, or citations. If information is uncertain, say so.
====================================================
""".strip()


# ══════════════════════════════════════════════════════════════════════════════
# 2.  REJECTION MESSAGES
# ══════════════════════════════════════════════════════════════════════════════

IMAGE_REJECTION_MESSAGE = (
    "I am Prakarna AI, a specialized Indian Legal Research Assistant. "
    "This uploaded image appears to be outside my domain of legal and academic assistance, "
    "so I cannot analyse or interpret it.\n\n"
    "If you upload a legal document, court order, statute, judgment, legal notice, contract, "
    "academic certificate, or law-related material, I will be happy to help."
)

GENERAL_REJECTION_MESSAGE = (
    "I am Prakarna AI, built exclusively for Indian law, IKS jurisprudence, legal education, "
    "and legal/academic document support. I cannot help with that request.\n\n"
    "I can help you analyse a legal issue, explain a statute or case, apply IRAC/FILAC/IDAR "
    "frameworks, read a legal document, or guide you on legal education and career paths."
)


# ══════════════════════════════════════════════════════════════════════════════
# 3.  NON-LEGAL CONTENT DETECTION — used by the domain classifier
# ══════════════════════════════════════════════════════════════════════════════

# Medical / health keywords that indicate a non-legal image or query
MEDICAL_KEYWORDS = {
    "mri", "x-ray", "xray", "ct scan", "ct-scan", "ctscan", "ecg", "ekg",
    "ultrasound", "sonography", "radiology", "radiograph", "mammogram",
    "diagnosis", "prognosis", "prescription", "dosage", "medication",
    "symptom", "pathology", "biopsy", "tumor", "tumour", "malignant",
    "benign", "fracture", "lesion", "brain scan", "chest scan",
    "blood report", "blood test", "hemoglobin", "platelet",
    "white matter", "grey matter", "gray matter", "cerebral",
    "axial", "sagittal", "coronal", "dicom", "flair",
}

# General non-legal content keywords
NON_LEGAL_CONTENT_KEYWORDS = {
    "recipe", "cooking", "ingredient", "calories", "nutrition",
    "cricket", "football", "hockey", "ipl", "match score",
    "movie", "bollywood", "hollywood", "song", "lyrics", "album",
    "stock market", "nifty", "sensex", "bitcoin", "crypto", "trading",
    "workout", "gym", "exercise", "diet plan", "weight loss",
    "gaming", "minecraft", "fortnite", "pubg", "valorant",
    "weather", "forecast", "temperature",
    "travel", "flight", "hotel", "booking",
    "programming", "python tutorial", "javascript", "react tutorial",
}

# Patterns that indicate a medical/radiology image was OCR'd
MEDICAL_IMAGE_PATTERNS = [
    r"\b(mri|ct scan|x[\-\s]?ray|ecg|ekg|ultrasound|radiology|dicom)\b",
    r"\b(axial|sagittal|coronal|flair|t1|t2)\b",
    r"\b(diagnosis|pathology|biopsy|lesion|fracture|tumor|tumour)\b",
    r"\b(white matter|grey matter|gray matter|cerebral|ventricle)\b",
    r"\b(blood report|hemoglobin|platelet|wbc|rbc)\b",
    r"\b(prescription|dosage|medication|mg|tablet|capsule)\b",
]


def contains_medical_content(text: str) -> bool:
    """Check if OCR-extracted text from an attachment contains medical content."""
    lower = (text or "").lower()
    # Check keyword set
    if any(kw in lower for kw in MEDICAL_KEYWORDS):
        return True
    # Check regex patterns
    if any(re.search(p, lower) for p in MEDICAL_IMAGE_PATTERNS):
        return True
    return False


def contains_non_legal_content(text: str) -> bool:
    """Check if text contains clearly non-legal content."""
    lower = (text or "").lower()
    return any(kw in lower for kw in NON_LEGAL_CONTENT_KEYWORDS)


def is_attachment_legal_or_academic(ocr_text: str) -> bool:
    """Determine if an attachment's OCR text suggests legal/academic content.
    
    Returns True if the content appears legal/academic,
    False if it appears medical or otherwise non-legal.
    """
    if contains_medical_content(ocr_text):
        return False
    # If no clear non-legal signal, assume it could be legal
    return True
