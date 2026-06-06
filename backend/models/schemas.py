from pydantic import BaseModel
from typing import List, Optional

# ── Chat ──────────────────────────────────────────────────────────────────────

class Message(BaseModel):
    role: str        # "user" | "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[Message] = []
    session_id: Optional[str] = None
    level: Optional[str] = None  # "beginner" | "intermediate" | "advanced" | "practitioner"

class Citation(BaseModel):
    """Structured citation with full source information."""
    source_type: str     # "IKS" | "Statute" | "Case" | "Principle"
    document: str        # e.g. "Manusmriti", "BNS 2023", "Kesavananda Bharati"
    section: str = ""    # e.g. "Chapter VIII, Verse 308" or "Section 103"
    page: str = ""       # e.g. "p.156" — populated when PDF is available
    citation_str: str    # Full formatted citation string for display

class Source(BaseModel):
    title: str
    type: str        # "case" | "statute" | "glossary" | "iks"
    citation: str
    page: str = ""
    excerpt: str = ""    # Relevant excerpt from source

class ChatResponse(BaseModel):
    intent: str
    answer: str
    sources: List[Source] = []
    citations: List[Citation] = []

# ── Ingest ────────────────────────────────────────────────────────────────────

class IngestResponse(BaseModel):
    status: str
    chunks_created: int
    collection: str
    filename: str

# ── Glossary ──────────────────────────────────────────────────────────────────

class GlossaryResponse(BaseModel):
    term: str
    definition: str
    example: str

# ── Search ────────────────────────────────────────────────────────────────────

class SearchResult(BaseModel):
    title: str
    snippet: str
    type: str        # "case" | "statute"

class SearchResponse(BaseModel):
    results: List[SearchResult]

# ── Templates ─────────────────────────────────────────────────────────────────

class Template(BaseModel):
    name: str
    structure: List[str]

class TemplatesResponse(BaseModel):
    templates: List[Template]

# ── Chat Sessions ─────────────────────────────────────────────────────────────

class ChatSession(BaseModel):
    session_id: str
    title: str
    last_active: str
    message_count: int

class ChatSessionList(BaseModel):
    sessions: List[ChatSession]

# ── Auth ──────────────────────────────────────────────────────────────────────

class UserProfile(BaseModel):
    uid: str
    email: str
    name: str = ""
    picture: str = ""
    level: str = "beginner"
    institution: str = ""
    year_of_study: str = ""
    areas_of_interest: List[str] = []

# ── Profile ───────────────────────────────────────────────────────────────────

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    level: Optional[str] = None          # "beginner" | "intermediate" | "advanced" | "practitioner"
    institution: Optional[str] = None
    year_of_study: Optional[str] = None
    areas_of_interest: Optional[List[str]] = None

# ── Feedback ──────────────────────────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    message_id: Optional[str] = None      # ID of the message being rated
    session_id: Optional[str] = None
    feedback_type: str                    # "thumbs_up" | "thumbs_down" | "bug_report" | "feature_request"
    comment: str = ""
    query: str = ""                       # The original query (for context)
    response: str = ""                    # The AI response (for context)

class FeedbackResponse(BaseModel):
    status: str
    feedback_id: str

# ── Share ─────────────────────────────────────────────────────────

class ShareChatRequest(BaseModel):
    title: str = ""
    messages: list = []

class ShareChatResponse(BaseModel):
    share_id: str
    share_url: str

