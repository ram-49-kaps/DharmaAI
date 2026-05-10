"""
DharmaAI v2 — FastAPI Backend
RAG-first legal AI for Indian jurisprudence with IKS integration.
"""

import logging
import os
import sys
import uuid

# Ensure backend root is on path
sys.path.insert(0, os.path.dirname(__file__))

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

from models.schemas import (
    ChatRequest, ChatResponse, Source, Citation,
    GlossaryResponse,
    SearchResponse, SearchResult,
    TemplatesResponse, Template,
    ChatSession, ChatSessionList,
    IngestResponse,
    UserProfile,
)
from db.database import init_db, get_connection
from db.seed import seed, seed_chromadb
from services.rag_engine import get_rag_engine
from services.knowledge_graph import get_knowledge_graph
from auth.firebase_auth import init_firebase, get_current_user, get_admin_user
from chains.router import detect_intent
from chains.definition import run_definition_chain
from chains.caselaw import run_caselaw_chain
from chains.statute import run_statute_chain
from chains.irac import run_irac_chain
from chains.idar import run_idar_chain
from chains.general_qa import run_general_chain
from chains.follow_up import run_follow_up_chain, is_follow_up
from chains.conversational import run_conversational_chain


# ── Startup ───────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("[Startup] Initialising DB …")
    init_db()
    seed()

    logger.info("[Startup] Initialising Firebase …")
    init_firebase()

    logger.info("[Startup] Building Knowledge Graph …")
    kg = get_knowledge_graph()
    summary = kg.get_graph_summary()
    logger.info(f"[Startup] KG ready — {summary['total_nodes']} nodes, {summary['total_edges']} edges ✓")

    logger.info("[Startup] Warming up RAG engine …")
    try:
        engine = get_rag_engine()
        # Check if ChromaDB has data; if not, seed it
        total = sum(engine.collection_count(c) for c in ["iks_texts", "modern_law", "case_law", "glossary"])
        if total == 0:
            logger.info("[Startup] ChromaDB empty — seeding corpus …")
            seed_chromadb()
            total = sum(engine.collection_count(c) for c in ["iks_texts", "modern_law", "case_law", "glossary"])
        else:
            logger.info(f"[Startup] ChromaDB already populated — skipping re-seed (saves API quota)")
        logger.info(f"[Startup] RAG ready — {total} documents in ChromaDB ✓")
    except Exception as exc:
        logger.error(f"[Startup] RAG engine warning: {exc}")
        logger.warning("[Startup] RAG degraded — continuing without full vector search")

    logger.info("[Startup] DharmaAI v2 ready ✓")
    yield


app = FastAPI(
    title="DharmaAI v2 — Legal Chatbot API",
    description="RAG-first Indian legal AI with IKS integration",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include ingest router
from api.ingest import router as ingest_router
app.include_router(ingest_router)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _save_message(session_id: str, user_id: str, role: str, content: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO chat_history (session_id, user_id, role, content) VALUES (?, ?, ?, ?)",
        (session_id, user_id, role, content)
    )
    conn.commit()
    conn.close()


def _sources_to_citations(sources: list) -> list:
    """Convert Source objects to Citation objects."""
    citations = []
    for s in sources:
        citations.append(Citation(
            source_type=s.type.upper(),
            document=s.title,
            section="",
            page=getattr(s, "page", ""),
            citation_str=s.citation or s.title,
        ))
    return citations


# ── Chat ──────────────────────────────────────────────────────────────────────

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, user: dict = Depends(get_current_user)):
    """RAG-first chat endpoint. All queries retrieve before generating."""
    try:
        history_dicts = [m.model_dump() for m in req.history]

        # Check for follow-up first (overrides router for continuation queries)
        if is_follow_up(req.message) and history_dicts:
            intent = "follow_up"
            answer = run_follow_up_chain(req.message, history_dicts)
        else:
            intent = detect_intent(req.message)

            if intent == "definition":
                answer = run_definition_chain(req.message)
            elif intent == "case_lookup":
                answer = run_caselaw_chain(req.message)
            elif intent == "statute_lookup":
                answer = run_statute_chain(req.message)
            elif intent == "irac_analysis":
                answer = run_irac_chain(req.message)
            elif intent == "idar_analysis":
                answer = run_idar_chain(req.message)
            elif intent == "comparative":
                answer = run_general_chain(req.message, history_dicts)
            elif intent == "conversational":
                answer = run_conversational_chain(req.message)
            else:
                answer = run_general_chain(req.message, history_dicts)

        # Retrieve sources for the response panel
        sources = []
        citations = []
        
        # Bypass heavy RAG retrieval if it's just a conversational greeting
        if intent != "conversational":
            engine = get_rag_engine()
            _, raw_results = engine.retrieve(req.message, k_final=8)
            seen = set()
            for r in raw_results:
                meta = r.get("metadata", {})
                title = meta.get("title", "")
                if title in seen:
                    continue
                seen.add(title)
                sources.append(Source(
                    title=title,
                    type=meta.get("source_type", meta.get("category", "statute")).lower(),
                    citation=meta.get("citation", ""),
                    page=meta.get("page", ""),
                    excerpt=r.get("content", "")[:200],
                ))

            citations = _sources_to_citations(sources)

        uid = user.get("uid", "anonymous")
        if req.session_id:
            _save_message(req.session_id, uid, "user", req.message)
            _save_message(req.session_id, uid, "assistant", answer)

        return ChatResponse(intent=intent, answer=answer, sources=sources, citations=citations)

    except Exception as exc:
        logger.error(f"[Chat] Error: {exc}", exc_info=True)
        # Graceful handling for rate-limit / quota errors
        exc_str = str(exc)
        if "429" in exc_str or "RESOURCE_EXHAUSTED" in exc_str:
            raise HTTPException(
                status_code=429,
                detail="The AI service is temporarily rate-limited. Please wait a minute and try again.",
            )
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred while processing your request. Please try again.",
        )


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.get("/api/me", response_model=UserProfile)
async def get_me(user: dict = Depends(get_current_user)):
    """Return current user profile."""
    return UserProfile(
        uid=user.get("uid", ""),
        email=user.get("email", ""),
        name=user.get("name", ""),
        picture=user.get("picture", ""),
    )


# ── Chat History ──────────────────────────────────────────────────────────────

@app.get("/api/sessions", response_model=ChatSessionList)
async def list_sessions(user: dict = Depends(get_current_user)):
    """List sessions for the current user."""
    uid = user.get("uid", "anonymous")
    conn = get_connection()
    rows = conn.execute("""
        SELECT session_id,
               MIN(content) AS first_message,
               MAX(created_at) AS last_active,
               COUNT(*) AS message_count
        FROM chat_history
        WHERE role = 'user' AND user_id = ?
        GROUP BY session_id
        ORDER BY MAX(created_at) DESC
        LIMIT 50
    """, (uid,)).fetchall()
    conn.close()

    sessions = []
    for r in rows:
        title = r["first_message"] or "Untitled"
        if len(title) > 40:
            title = title[:40] + "..."
        sessions.append(ChatSession(
            session_id=r["session_id"],
            title=title,
            last_active=r["last_active"] or "",
            message_count=r["message_count"],
        ))
    return ChatSessionList(sessions=sessions)


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str, user: dict = Depends(get_current_user)):
    uid = user.get("uid", "anonymous")
    conn = get_connection()
    rows = conn.execute(
        "SELECT role, content, created_at FROM chat_history "
        "WHERE session_id = ? AND user_id = ? ORDER BY created_at",
        (session_id, uid)
    ).fetchall()
    conn.close()
    if not rows:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session_id,
        "messages": [{"role": r["role"], "content": r["content"], "created_at": r["created_at"]} for r in rows],
    }


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str, user: dict = Depends(get_current_user)):
    uid = user.get("uid", "anonymous")
    conn = get_connection()
    conn.execute("DELETE FROM chat_history WHERE session_id = ? AND user_id = ?", (session_id, uid))
    conn.commit()
    conn.close()
    return {"status": "deleted"}


# ── Glossary ──────────────────────────────────────────────────────────────────

@app.get("/api/glossary/{term}", response_model=GlossaryResponse)
async def get_glossary(term: str, user: dict = Depends(get_current_user)):
    conn = get_connection()
    row = conn.execute(
        "SELECT term, definition, example FROM glossary WHERE LOWER(term) = LOWER(?)", (term,)
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail=f"Term '{term}' not found in glossary")
    return GlossaryResponse(term=row["term"], definition=row["definition"], example=row["example"])


@app.get("/api/glossary")
async def list_glossary(user: dict = Depends(get_current_user)):
    conn = get_connection()
    rows = conn.execute("SELECT term FROM glossary ORDER BY term").fetchall()
    conn.close()
    return {"terms": [r["term"] for r in rows]}


# ── Search ────────────────────────────────────────────────────────────────────

@app.get("/api/search", response_model=SearchResponse)
async def search(q: str = Query(..., min_length=1), user: dict = Depends(get_current_user)):
    conn = get_connection()
    pattern = f"%{q}%"
    cases = conn.execute(
        "SELECT title, citation, snippet FROM cases WHERE title LIKE ? OR snippet LIKE ? LIMIT 5",
        (pattern, pattern)
    ).fetchall()
    statutes = conn.execute(
        "SELECT title, citation, snippet FROM statutes WHERE title LIKE ? OR snippet LIKE ? LIMIT 5",
        (pattern, pattern)
    ).fetchall()
    conn.close()

    results = []
    for r in cases:
        results.append(SearchResult(title=r["title"], snippet=r["snippet"] or "", type="case"))
    for r in statutes:
        results.append(SearchResult(title=r["title"], snippet=r["snippet"] or "", type="statute"))
    return SearchResponse(results=results)


# ── Templates ─────────────────────────────────────────────────────────────────

@app.get("/api/templates", response_model=TemplatesResponse)
async def get_templates():
    return TemplatesResponse(templates=[
        Template(name="IRAC", structure=["Issue", "Rule", "Application", "Conclusion"]),
        Template(name="CRAC", structure=["Conclusion", "Rule", "Application", "Conclusion"]),
        Template(name="CREAC", structure=["Conclusion", "Rule", "Explanation", "Application", "Conclusion"]),
        Template(name="IDAR", structure=["Issue", "Dharma (applicable rule)", "Application of Danda", "Resolution"]),
    ])


# ── Knowledge Graph ───────────────────────────────────────────────────────────

@app.get("/api/knowledge-graph")
async def knowledge_graph_summary():
    kg = get_knowledge_graph()
    return kg.get_graph_summary()


@app.get("/api/knowledge-graph/{node_id}")
async def knowledge_graph_node(node_id: str, user: dict = Depends(get_current_user)):
    kg = get_knowledge_graph()
    node = kg.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found in KG")
    return {
        "node": {"id": node.id, "label": node.label, "category": node.category,
                 "description": node.description, "era": node.era, "source": node.source_text},
        "relationships": kg.get_relationships(node_id),
        "related": [{"id": n.id, "label": n.label, "category": n.category}
                    for n in kg.get_related(node_id, max_depth=2)],
    }


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    kg = get_knowledge_graph()
    summary = kg.get_graph_summary()
    try:
        engine = get_rag_engine()
        rag_counts = {c: engine.collection_count(c) for c in ["iks_texts", "modern_law", "case_law", "glossary"]}
    except Exception:
        rag_counts = {}

    return {
        "status": "ok",
        "model": "DharmaAI v2.0",
        "knowledge_graph": {
            "nodes": summary["total_nodes"],
            "edges": summary["total_edges"],
        },
        "chromadb": rag_counts,
    }
