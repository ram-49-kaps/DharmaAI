from pydantic import BaseModel
from typing import List, Optional

# ── Chat ──────────────────────────────────────────────────────────────────────

class Message(BaseModel):
    role: str        # "user" | "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[Message] = []
    session_id: Optional[str] = None   # if provided, messages are persisted

class Source(BaseModel):
    title: str
    type: str        # "case" | "statute" | "glossary"
    citation: str

class ChatResponse(BaseModel):
    intent: str
    answer: str
    sources: List[Source] = []

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
