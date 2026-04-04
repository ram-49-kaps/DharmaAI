import os
import sys
import uuid

# ensure backend root is on path
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

from models.schemas import (
    ChatRequest, ChatResponse, Source,
    GlossaryResponse,
    SearchResponse, SearchResult,
    TemplatesResponse, Template,
    ChatSession, ChatSessionList,
)
from db.database import init_db
from db.seed import seed
from services.rag import get_vector_store
from services.knowledge_graph import get_knowledge_graph
from chains.router import detect_intent
from chains.definition import run_definition_chain
from chains.caselaw import run_caselaw_chain
from chains.statute import run_statute_chain
from chains.irac import run_irac_chain
from chains.idar import run_idar_chain
from chains.general_qa import run_general_chain
from db.database import get_connection


# ── Startup ───────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[Startup] Initialising DB …")
    init_db()
    seed()
    print("[Startup] Warming up ChromaDB …")
    get_vector_store()
    print("[Startup] Building Knowledge Graph …")
    kg = get_knowledge_graph()
    summary = kg.get_graph_summary()
    print(f"[Startup] KG ready — {summary['total_nodes']} nodes, {summary['total_edges']} edges ✓")
    print("[Startup] Ready ✓")
    yield


app = FastAPI(
    title="DharmaAI – Legal Chatbot API",
    description="LLM-powered educational legal assistant for Indian law students",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Chat ──────────────────────────────────────────────────────────────────────

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        intent = detect_intent(req.message)

        if intent == "definition":
            answer = run_definition_chain(req.message)
        elif intent == "case_law":
            answer = run_caselaw_chain(req.message)
        elif intent == "statute":
            answer = run_statute_chain(req.message)
        elif intent == "legal_reasoning":
            answer = run_irac_chain(req.message)
        elif intent == "idar":
            answer = run_idar_chain(req.message)
        else:
            answer = run_general_chain(req.message, [m.model_dump() for m in req.history])

        # retrieve sources from vector store
        from services.rag import retrieve_sources
        sources = retrieve_sources(req.message, k=3)

        # persist to chat_history if session_id provided
        if req.session_id:
            _save_message(req.session_id, "user", req.message)
            _save_message(req.session_id, "assistant", answer)

        return ChatResponse(intent=intent, answer=answer, sources=sources)

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


def _save_message(session_id: str, role: str, content: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO chat_history (session_id, role, content) VALUES (?, ?, ?)",
        (session_id, role, content)
    )
    conn.commit()
    conn.close()


# ── Chat History Persistence ──────────────────────────────────────────────────

@app.get("/api/sessions", response_model=ChatSessionList)
async def list_sessions():
    conn = get_connection()
    rows = conn.execute("""
        SELECT session_id,
               MIN(content) AS first_message,
               MAX(created_at) AS last_active,
               COUNT(*) AS message_count
        FROM chat_history
        WHERE role = 'user'
        GROUP BY session_id
        ORDER BY MAX(created_at) DESC
        LIMIT 50
    """).fetchall()
    conn.close()

    sessions = []
    for r in rows:
        title = r["first_message"]
        if len(title) > 30:
            title = title[:30] + "..."
        sessions.append(ChatSession(
            session_id=r["session_id"],
            title=title,
            last_active=r["last_active"],
            message_count=r["message_count"],
        ))
    return ChatSessionList(sessions=sessions)


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    conn = get_connection()
    rows = conn.execute(
        "SELECT role, content, created_at FROM chat_history WHERE session_id = ? ORDER BY created_at",
        (session_id,)
    ).fetchall()
    conn.close()
    if not rows:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session_id,
        "messages": [{"role": r["role"], "content": r["content"], "created_at": r["created_at"]} for r in rows],
    }


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    conn = get_connection()
    conn.execute("DELETE FROM chat_history WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()
    return {"status": "deleted"}


# ── Glossary ──────────────────────────────────────────────────────────────────

@app.get("/api/glossary/{term}", response_model=GlossaryResponse)
async def get_glossary(term: str):
    conn = get_connection()
    cur  = conn.cursor()
    row  = cur.execute(
        "SELECT term, definition, example FROM glossary WHERE LOWER(term) = LOWER(?)",
        (term,)
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail=f"Term '{term}' not found in glossary")
    return GlossaryResponse(term=row["term"], definition=row["definition"], example=row["example"])


@app.get("/api/glossary", response_model=dict)
async def list_glossary():
    conn = get_connection()
    rows = conn.execute("SELECT term FROM glossary ORDER BY term").fetchall()
    conn.close()
    return {"terms": [r["term"] for r in rows]}


# ── Search ────────────────────────────────────────────────────────────────────

@app.get("/api/search", response_model=SearchResponse)
async def search(q: str = Query(..., min_length=1)):
    conn    = get_connection()
    cur     = conn.cursor()
    pattern = f"%{q}%"

    cases = cur.execute(
        "SELECT title, citation, snippet FROM cases WHERE title LIKE ? OR snippet LIKE ? LIMIT 5",
        (pattern, pattern)
    ).fetchall()

    statutes = cur.execute(
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
        Template(name="IRAC",  structure=["Issue", "Rule", "Application", "Conclusion"]),
        Template(name="CRAC",  structure=["Conclusion", "Rule", "Application", "Conclusion"]),
        Template(name="CREAC", structure=["Conclusion", "Rule", "Explanation", "Application", "Conclusion"]),
        Template(name="IDAR",  structure=["Issue", "Dharma (applicable rule)", "Application of Danda", "Resolution"]),
    ])


# ── Knowledge Graph ───────────────────────────────────────────────────────────

@app.get("/api/knowledge-graph")
async def knowledge_graph_summary():
    kg = get_knowledge_graph()
    return kg.get_graph_summary()


@app.get("/api/knowledge-graph/{node_id}")
async def knowledge_graph_node(node_id: str):
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
    return {
        "status": "ok",
        "model": "DharmaAI v1.0",
        "knowledge_graph": {
            "nodes": summary["total_nodes"],
            "edges": summary["total_edges"],
        },
    }
