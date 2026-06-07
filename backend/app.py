"""
DharmaAI v2 — FastAPI Backend
RAG-first legal AI for Indian jurisprudence with IKS integration.
"""

import logging
import json
import os
import sys
import tempfile
import uuid

# Ensure backend root is on path
sys.path.insert(0, os.path.dirname(__file__))

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query, Depends, Request, UploadFile
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
    ThinkingRequest,
    GlossaryResponse,
    SearchResponse, SearchResult,
    TemplatesResponse, Template,
    ChatSession, ChatSessionList,
    IngestResponse,
    UserProfile,
    ProfileUpdate,
    FeedbackRequest,
    FeedbackResponse,
    ShareChatRequest,
    ShareChatResponse,
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
from chains.filac import run_filac_chain
from chains.idar import run_idar_chain
from chains.general_qa import run_general_chain
from chains.follow_up import run_follow_up_chain, is_follow_up
from chains.conversational import run_conversational_chain
from chains.thinking import run_thinking_steps_chain
from services.pdf_ingestion import PDFIngestor


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


def _user_profile_from_row(row, user: dict) -> UserProfile:
    if not row:
        return UserProfile(
            uid=user.get("uid", ""),
            email=user.get("email", ""),
            name=user.get("name", ""),
            picture=user.get("picture", ""),
        )
    try:
        interests = json.loads(row["areas_of_interest"] or "[]")
    except json.JSONDecodeError:
        interests = []
    return UserProfile(
        uid=row["uid"],
        email=row["email"],
        name=row["name"],
        picture=row["picture"],
        level=row["level"],
        institution=row["institution"],
        year_of_study=row["year_of_study"],
        areas_of_interest=interests,
    )


def _get_saved_profile(uid: str, user: dict) -> UserProfile:
    conn = get_connection()
    row = conn.execute("SELECT * FROM user_profiles WHERE uid = ?", (uid,)).fetchone()
    conn.close()
    return _user_profile_from_row(row, user)


async def _extract_attachment_context(files: list[UploadFile]) -> str:
    """Extract readable context from chat attachments without storing them permanently."""
    if not files:
        return ""

    sections = []
    for file in files[:10]:
        content = await file.read()
        if len(content) > 20 * 1024 * 1024:
            raise HTTPException(status_code=413, detail=f"{file.filename} is too large (max 20 MB)")

        content_type = (file.content_type or "").lower()
        filename = file.filename or "attachment"
        lower_name = filename.lower()

        if lower_name.endswith(".pdf") or content_type == "application/pdf":
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            try:
                pages = PDFIngestor().extract_with_metadata(tmp_path)
                text = "\n\n".join(f"[Page {page}] {page_text}" for page_text, page in pages)
                if len(text) > 12000:
                    text = text[:12000] + "\n...[PDF text truncated]"
                sections.append(f"Attachment: {filename} (PDF)\n{text or '[No text extracted]'}")
            finally:
                os.unlink(tmp_path)
        elif content_type.startswith("image/") or lower_name.endswith((".png", ".jpg", ".jpeg", ".webp")):
            import io
            from PIL import Image
            import pytesseract

            # Ensure pytesseract can find tesseract on macOS / common paths
            tesseract_paths = [
                '/opt/homebrew/bin/tesseract',
                '/usr/local/bin/tesseract',
                '/usr/bin/tesseract'
            ]
            for path in tesseract_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    break

            try:
                image = Image.open(io.BytesIO(content))
                extracted_text = pytesseract.image_to_string(image)
                extracted_text = (extracted_text or "").strip()
                
                if extracted_text:
                    if len(extracted_text) > 12000:
                        extracted_text = extracted_text[:12000] + "\n...[OCR text truncated]"
                    sections.append(
                        f"Attachment: {filename} (Image OCR Text):\n{extracted_text}"
                    )
                else:
                    sections.append(
                        f"Attachment: {filename} (Image):\n[No text could be extracted or identified in this image via OCR.]"
                    )
            except Exception as e:
                logger.error(f"OCR failed for {filename}: {e}", exc_info=True)
                sections.append(
                    f"Attachment: {filename} (Image):\n[Error performing OCR extraction: {str(e)}]"
                )
        elif content_type.startswith("text/") or lower_name.endswith(".txt"):
            text = content.decode("utf-8", errors="replace")
            if len(text) > 12000:
                text = text[:12000] + "\n...[text attachment truncated]"
            sections.append(f"Attachment: {filename} (text)\n{text}")
        else:
            sections.append(
                f"Attachment: {filename} ({content_type or 'unknown'}, {len(content)} bytes). "
                "This file type was received but cannot yet be text-extracted."
            )

    return "\n\n".join(sections)


@app.post("/api/thinking")
async def get_thinking_steps(req: ThinkingRequest, user: dict = Depends(get_current_user)):
    """Fast endpoint to generate 3 custom thinking steps for a query."""
    try:
        steps = run_thinking_steps_chain(req.query)
        return steps
    except Exception as e:
        logger.error(f"[Thinking] API Error: {e}")
        return [
            "Analyzing legal query...",
            "Searching jurisprudential records...",
            "Preparing comprehensive synthesis..."
        ]


async def _chat_request_from_request(request: Request) -> ChatRequest:
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        message = str(form.get("message") or "")
        history_raw = form.get("history") or "[]"
        try:
            history = json.loads(history_raw) if isinstance(history_raw, str) else []
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="history must be valid JSON")

        files = []
        for key in ("files", "file", "attachments"):
            files.extend([item for item in form.getlist(key) if hasattr(item, "filename") and hasattr(item, "read")])
        attachment_context = await _extract_attachment_context(files)
        if attachment_context:
            message = (
                f"{message}\n\n"
                "--- ATTACHMENT DETAILS ---\n"
                "The user has attached one or more files. The text below shows the contents of those attachments (for images/screenshots, this is the text extracted via OCR).\n"
                "Treat this extracted text as the true contents of the attachment. Do NOT apologize, do NOT state that you cannot see the image, and do NOT mention that you are a text-only model. Instead, directly answer the user's query about the attachment using the text provided below.\n\n"
                f"{attachment_context}"
            ).strip()

        return ChatRequest(
            message=message,
            history=history,
            session_id=form.get("session_id") or None,
            level=form.get("level") or None,
        )

    body = await request.json()
    return ChatRequest(**body)


# ── Chat ──────────────────────────────────────────────────────────────────────

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: Request, user: dict = Depends(get_current_user)):
    """RAG-first chat endpoint. All queries retrieve before generating."""
    req = await _chat_request_from_request(request)
    try:
        history_dicts = [m.model_dump() for m in req.history]
        level = req.level or _get_saved_profile(user.get("uid", "anonymous"), user).level

        # Check for follow-up first (overrides router for continuation queries)
        if is_follow_up(req.message) and history_dicts:
            intent = "follow_up"
            answer = run_follow_up_chain(req.message, history_dicts, level=level)
        else:
            intent = detect_intent(req.message)

            if intent == "definition":
                answer = run_definition_chain(req.message, level=level)
            elif intent == "case_lookup":
                answer = run_caselaw_chain(req.message, level=level)
            elif intent == "statute_lookup":
                answer = run_statute_chain(req.message, level=level)
            elif intent == "irac_analysis":
                answer = run_irac_chain(req.message, level=level)
            elif intent == "filac_analysis":
                answer = run_filac_chain(req.message, level=level)
            elif intent == "idar_analysis":
                answer = run_idar_chain(req.message, level=level)
            elif intent == "comparative":
                answer = run_general_chain(req.message, history_dicts, level=level)
            elif intent == "conversational":
                answer = run_conversational_chain(req.message)
            else:
                answer = run_general_chain(req.message, history_dicts, level=level)

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

        # Generate suggested follow-up questions
        suggested_questions = []
        if intent != "conversational" and answer:
            from chains.follow_up import generate_suggested_questions
            suggested = generate_suggested_questions(req.message, answer)
            if suggested:
                for line in suggested.split("\n"):
                    line_clean = line.strip()
                    if line_clean.startswith(("- ", "* ")):
                        q = line_clean[2:].strip()
                        if q:
                            suggested_questions.append(q)
                    elif len(line_clean) > 3 and line_clean[0].isdigit() and line_clean[1:3] == ". ":
                        q = line_clean[3:].strip()
                        if q:
                            suggested_questions.append(q)
                
                # Limit to exactly 2 questions as per specifications
                suggested_questions = suggested_questions[:2]

        uid = user.get("uid", "anonymous")
        if req.session_id:
            _save_message(req.session_id, uid, "user", req.message)
            _save_message(req.session_id, uid, "assistant", answer)

        return ChatResponse(
            intent=intent, 
            answer=answer, 
            sources=sources, 
            citations=citations,
            suggested_questions=suggested_questions
        )

    except Exception as exc:
        logger.error(f"[Chat] Error: {exc}", exc_info=True)
        exc_str = str(exc)
        
        # Check for specific rate limit indicators
        is_rate_limited = any(x in exc_str for x in ["429", "RESOURCE_EXHAUSTED", "Rate Limited"])
        
        if is_rate_limited:
            # DharmaAI Lite Mode — don't crash, just inform.
            lite_answer = (
                "**[DharmaAI Lite Mode Active]**\n\n"
                "I am currently experiencing extremely high traffic or API rate limits (likely due to background database seeding). "
                "While I cannot perform a deep legal retrieval at this exact second, I can tell you that I've received your query: "
                f"\"{req.message[:50]}...\"\n\n"
                "Please wait about 60 seconds for the quota to reset and try again for a full detailed analysis."
            )
            return ChatResponse(
                intent="general_qa",
                answer=lite_answer,
                sources=[],
                citations=[]
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


@app.get("/api/profile", response_model=UserProfile)
async def get_profile(user: dict = Depends(get_current_user)):
    """Return the persisted profile for the current user."""
    uid = user.get("uid", "anonymous")
    return _get_saved_profile(uid, user)


@app.put("/api/profile", response_model=UserProfile)
async def update_profile(payload: ProfileUpdate, user: dict = Depends(get_current_user)):
    """Create or update the current user's profile."""
    uid = user.get("uid", "anonymous")
    existing = _get_saved_profile(uid, user)

    updated = {
        "email": user.get("email", existing.email),
        "name": payload.name if payload.name is not None else existing.name,
        "picture": user.get("picture", existing.picture),
        "level": payload.level if payload.level is not None else existing.level,
        "institution": payload.institution if payload.institution is not None else existing.institution,
        "year_of_study": payload.year_of_study if payload.year_of_study is not None else existing.year_of_study,
        "areas_of_interest": payload.areas_of_interest
        if payload.areas_of_interest is not None
        else existing.areas_of_interest,
    }

    allowed_levels = {"beginner", "intermediate", "advanced", "practitioner"}
    if updated["level"] not in allowed_levels:
        raise HTTPException(status_code=400, detail=f"level must be one of {sorted(allowed_levels)}")

    conn = get_connection()
    conn.execute(
        """
        INSERT INTO user_profiles
            (uid, email, name, picture, level, institution, year_of_study, areas_of_interest, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(uid) DO UPDATE SET
            email = excluded.email,
            name = excluded.name,
            picture = excluded.picture,
            level = excluded.level,
            institution = excluded.institution,
            year_of_study = excluded.year_of_study,
            areas_of_interest = excluded.areas_of_interest,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            uid,
            updated["email"],
            updated["name"],
            updated["picture"],
            updated["level"],
            updated["institution"],
            updated["year_of_study"],
            json.dumps(updated["areas_of_interest"]),
        ),
    )
    conn.commit()
    conn.close()
    return _get_saved_profile(uid, user)


@app.post("/api/feedback", response_model=FeedbackResponse)
async def create_feedback(payload: FeedbackRequest, user: dict = Depends(get_current_user)):
    """Store user feedback on answers or product issues."""
    allowed_types = {"thumbs_up", "thumbs_down", "bug_report", "feature_request"}
    if payload.feedback_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"feedback_type must be one of {sorted(allowed_types)}")

    uid = user.get("uid", "anonymous")
    conn = get_connection()
    cur = conn.execute(
        """
        INSERT INTO feedback
            (user_id, message_id, session_id, feedback_type, comment, query, response)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            uid,
            payload.message_id,
            payload.session_id,
            payload.feedback_type,
            payload.comment,
            payload.query,
            payload.response,
        ),
    )
    conn.commit()
    feedback_id = str(cur.lastrowid)
    conn.close()
    return FeedbackResponse(status="success", feedback_id=feedback_id)


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
        Template(name="FILAC", structure=["Facts", "Issues", "Law", "Analysis", "Conclusion"]),
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


# ── Share Chat ────────────────────────────────────────────────────────────────

@app.post("/api/share", response_model=ShareChatResponse)
async def share_chat(payload: ShareChatRequest, request: Request, user: dict = Depends(get_current_user)):
    """Create a shareable link for a chat conversation."""
    uid = user.get("uid", "anonymous")
    share_id = uuid.uuid4().hex[:12]

    conn = get_connection()
    conn.execute(
        "INSERT INTO shared_chats (share_id, user_id, title, messages) VALUES (?, ?, ?, ?)",
        (share_id, uid, payload.title or "Shared Chat", json.dumps(payload.messages)),
    )
    conn.commit()
    conn.close()

    # Build the share URL from the request origin
    origin = request.headers.get("origin") or request.headers.get("referer", "").rstrip("/")
    if not origin:
        origin = "http://localhost:3000"
    share_url = f"{origin}?share={share_id}"

    return ShareChatResponse(share_id=share_id, share_url=share_url)


@app.get("/api/share/{share_id}")
async def get_shared_chat(share_id: str):
    """Public endpoint — no auth required. Returns shared chat data."""
    conn = get_connection()
    row = conn.execute(
        "SELECT share_id, title, messages, created_at FROM shared_chats WHERE share_id = ?",
        (share_id,)
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Shared chat not found")

    try:
        messages = json.loads(row["messages"])
    except json.JSONDecodeError:
        messages = []

    return {
        "share_id": row["share_id"],
        "title": row["title"],
        "messages": messages,
        "created_at": row["created_at"],
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
