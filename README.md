# ⚖️ DharmaAI v2 — Indian Legal AI Platform

RAG-first legal AI chatbot for Indian jurisprudence with deep IKS (Indian Knowledge System) integration.

**Primary LLM:** Gemini 2.0 Flash · **Embeddings:** Gemini text-embedding-004 · **Vector Store:** ChromaDB · **Auth:** Firebase

---

## What's New in v2

- **RAG-first**: every query retrieves from ChromaDB before the LLM answers — no hallucination
- **Gemini 2.0 Flash** replaces Groq as primary LLM; `max_tokens=4096` fixes cut-off responses
- **Firebase Authentication** — Google SSO + Email/Password; per-user chat history
- **Judge-Advocate agent** (LangGraph) verifies citations before returning answers
- **50+ node Knowledge Graph** with embedding-based matching (fixes "Danda everywhere" bug)
- **Router fixed** — defaults to `general_qa`, never auto-triggers IRAC for normal queries
- **PDF ingestion endpoint** — admin can upload PDFs at runtime
- **Structured seed corpus** — 13 IKS concepts, 10 modern law entries, 18 landmark cases
- **Citation system** — every answer cites `[Source | Document | Section | Page]`

---

## Quick Start

### 1. Prerequisites

```bash
python --version   # need 3.11+
node --version     # need 18+
```

Get API keys:
- **Gemini API key** → [aistudio.google.com/apikey](https://aistudio.google.com/apikey) (free)
- **Firebase project** → [console.firebase.google.com](https://console.firebase.google.com)
  - Enable Authentication → Google + Email/Password
  - Project Settings → Service Accounts → Generate private key (JSON)
  - Project Settings → General → Web app → copy config

### 2. Backend Setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env with your actual keys
```

`.env` file:
```
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key          # optional fallback
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxx@your-project.iam.gserviceaccount.com
ADMIN_USER_IDS=your_firebase_uid    # for PDF upload access
```

### 3. Frontend Setup

```bash
cd frontend
npm install

cp .env.example .env
# Edit .env with your Firebase web config
```

`.env` file:
```
REACT_APP_API_URL=http://localhost:8000
REACT_APP_FIREBASE_API_KEY=...
REACT_APP_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
REACT_APP_FIREBASE_PROJECT_ID=your-project-id
REACT_APP_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
REACT_APP_FIREBASE_MESSAGING_SENDER_ID=...
REACT_APP_FIREBASE_APP_ID=...
```

### 4. Run

**Terminal 1 — Backend:**
```bash
cd backend && venv\Scripts\activate
uvicorn app:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend && npm start
```

Open [http://localhost:3000](http://localhost:3000)

### 5. Seed the Knowledge Base

On first startup the backend automatically seeds ChromaDB from the JSON corpus files in `backend/data/seed_corpus/`. You can also run it manually:

```bash
cd backend
python -m db.seed
```

### 6. Ingest a PDF (Admin)

Via the UI: click **Upload PDF (Admin)** in the sidebar (only visible to admin users).

Via API:
```bash
curl -X POST http://localhost:8000/api/ingest \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -F "file=@danda.pdf" \
  -F "category=iks_texts"
```

Categories: `iks_texts` | `modern_law` | `case_law`

---

## Docker Compose (Full Stack)

```bash
cp backend/.env.example backend/.env   # fill in keys
cp frontend/.env.example frontend/.env # fill in keys

docker compose up --build
```

Frontend: [http://localhost:3000](http://localhost:3000)  
Backend: [http://localhost:8000](http://localhost:8000)  
API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Run Tests

```bash
cd backend
venv\Scripts\activate
pytest tests/ -v
```

Test coverage:
- `test_router.py` — intent classification (general queries must not trigger IRAC)
- `test_rag.py` — retrieval quality and ChromaDB operations
- `test_citations.py` — citation format and source metadata
- `test_judge_advocate.py` — LangGraph agent revision flow

---

## Architecture

```
User Query
    ↓
[Auth] Firebase ID token verified
    ↓
[Router] detect_intent() → general_qa (default), definition, case_lookup,
                            statute_lookup, irac_analysis, idar_analysis,
                            comparative, follow_up
    ↓
[RAG Engine] Gemini text-embedding-004
  → hybrid_search across 4 ChromaDB collections
    (iks_texts, modern_law, case_law, glossary)
  → rerank top-5 results
  → build_context with [Source | Doc | Section | Page] tags
    ↓
[Knowledge Graph] 50+ node IKS↔Modern law graph
  → embedding-based matching (threshold 0.4)
  → only injects Danda context for criminal law queries
    ↓
[Chain] Appropriate chain (general_qa / irac / idar / etc.)
  → Gemini 2.0 Flash, max_tokens=4096
  → STRICT: answer only from retrieved sources
    ↓
[Judge-Advocate] (LangGraph)
  → Advocate drafts → Judge critiques → revise ≤2x → finalize
    ↓
Response with citations + sources panel
```

---

## Seed Corpus

| Collection | File | Contents |
|---|---|---|
| `iks_texts` | `iks_concepts.json` | 13 IKS concepts (Dharma, Danda, Prāyaścitta, etc.) |
| `modern_law` | `modern_law_corpus.json` | BNS 2023, IPC, Constitution, Contract Act, Evidence Act, CrPC |
| `case_law` | `landmark_cases.json` | 18 landmark cases (Kesavananda, Maneka Gandhi, Puttaswamy, etc.) |
| `glossary` | *(from seed.py)* | 13 legal terms with IKS connections |
| `iks_modern_mappings.json` | *(cross-reference)* | 8 deep IKS→Modern law mappings |

When Law Dept provides PDFs, ingest via `/api/ingest` — no code changes needed.

---

## Bug Fixes from v1

| Bug | Fix |
|---|---|
| Responses cut off mid-sentence | `max_tokens` raised from 1024 → 4096 |
| Normal queries trigger IRAC | Router defaults to `general_qa`; IRAC only on explicit request |
| No conversation memory | `ConversationBufferWindowMemory` last 10 turns |
| Danda appears in unrelated topics | KG similarity threshold 0.4; Danda only injected for criminal law queries |
| Superficial IKS connections | Deep `iks_modern_mappings.json` with genuine explanations |
| Only 5 hardcoded cases | 18+ landmark cases in ChromaDB seed corpus |
| Brief responses | Gemini 2.0 Flash with detailed prompt instructions |
| No real citations | `[Source | Doc | Section | Page]` citation system throughout |

---

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | Yes | Gemini 2.0 Flash + embeddings |
| `GROQ_API_KEY` | No | Fallback LLM if no Gemini key |
| `FIREBASE_PROJECT_ID` | Yes | Firebase project |
| `FIREBASE_PRIVATE_KEY` | Yes | Service account private key |
| `FIREBASE_CLIENT_EMAIL` | Yes | Service account email |
| `ADMIN_USER_IDS` | No | Comma-separated UIDs for PDF upload |
