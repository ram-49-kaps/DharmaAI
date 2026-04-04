# ⚖️ DharmaAI – Jurisprudential Legal Chatbot
### Indian Knowledge System (IKS) × Modern Indian Law × LLM

---

## 🏗️ Architecture

```
User → React Frontend → FastAPI Backend
                              ├─ Intent Router (LangChain + Groq)
                              ├─ Specialized Chains (Definition / CaseLaw / Statute / IRAC / General)
                              ├─ RAG Pipeline (FAISS + HuggingFace Embeddings)
                              └─ SQLite DB (Glossary / Cases / Statutes / History)
```

---

## ⚙️ Backend Setup

### 1. Prerequisites
- Python 3.10+
- Free Groq API key → https://console.groq.com

### 2. Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Set up environment

```bash
cp .env.example .env
# Edit .env → add your GROQ_API_KEY
```

### 4. Run the server

```bash
uvicorn app:app --reload --port 8000
```

The server will automatically:
- Create SQLite tables
- Seed 10 glossary terms, 5 landmark cases, 6 statutes
- Build the FAISS vector index (first run takes ~30s)

### 5. Verify

Open http://localhost:8000/docs → Swagger UI with all endpoints

---

## 🎨 Frontend Setup

### 1. Prerequisites
- Node.js 18+

### 2. Install and run

```bash
cd frontend
npm install
npm start
```

Opens at http://localhost:3000 (proxies API to backend at :8000)

---

## 🔌 API Endpoints

| Method | Endpoint              | Description                    |
|--------|-----------------------|--------------------------------|
| POST   | /api/chat             | Main chat (intent + RAG)       |
| GET    | /api/glossary/{term}  | Look up a legal term           |
| GET    | /api/glossary         | List all glossary terms        |
| GET    | /api/search?q=        | Search cases & statutes        |
| GET    | /api/templates        | Get IRAC/IDAR templates        |
| GET    | /api/health           | Health check                   |

### Chat Request/Response (exact schema)

```json
// POST /api/chat
Request:  { "message": "string", "history": [{"role":"user","content":"string"}] }
Response: { "intent": "string", "answer": "string", "sources": [{"title":"string","type":"case|statute|glossary","citation":"string"}] }
```

---

## 🧠 Intent Routing

| Intent           | Triggered when asking about…         |
|------------------|--------------------------------------|
| definition       | What is mens rea / Dharma / IRAC?    |
| case_law         | Kesavananda Bharati / Maneka Gandhi  |
| statute          | IPC / Constitution / Contract Act    |
| legal_reasoning  | Apply IRAC to this scenario…         |
| general          | Everything else (RAG + memory)       |

---

## 📚 IKS Content Included

- **Dharma** – foundational Indian legal principle
- **Danda** – Kautilyan theory of sanction
- **Puruṣārtha** – situational ethics framework (Daya Krishna)
- **Arthashastra** – Kautilya's legal treatise (c. 3rd century BCE)
- **Dharmaśāstras** – Manu, Yājñavalkya, Nārada
- **IDAR Template** – Dharma-based IRAC variant

---

## 🔧 Troubleshooting

| Problem | Fix |
|---------|-----|
| GROQ_API_KEY error | Add key to backend/.env |
| FAISS build slow | Normal on first run; cached after |
| Frontend can't reach backend | Ensure backend runs on :8000 |
| Module not found | Run `pip install -r requirements.txt` |

---

## 📁 Project Structure

```
legal_chatbot/
├── backend/
│   ├── app.py                  # FastAPI main app
│   ├── requirements.txt
│   ├── .env.example
│   ├── chains/
│   │   ├── router.py           # Intent detection
│   │   ├── definition.py       # Definition chain
│   │   ├── caselaw.py          # Case law chain
│   │   ├── statute.py          # Statute chain
│   │   ├── irac.py             # IRAC reasoning chain
│   │   └── general_qa.py       # RAG + memory chain
│   ├── services/
│   │   ├── llm.py              # Groq LLM (cached)
│   │   └── rag.py              # FAISS pipeline
│   ├── db/
│   │   ├── database.py         # SQLite init
│   │   └── seed.py             # Seed data
│   ├── models/
│   │   └── schemas.py          # Pydantic models (shared contract)
│   └── data/
│       └── legal_docs.txt      # Source documents for RAG
└── frontend/
    ├── package.json
    ├── public/index.html
    └── src/
        ├── App.js              # Root component + state
        ├── App.css             # Full dark theme
        ├── index.js
        ├── components/
        │   ├── ChatWindow.jsx
        │   ├── MessageBubble.jsx
        │   ├── InputBox.jsx
        │   ├── Sidebar.jsx
        │   ├── SourcesPanel.jsx
        │   └── TemplatesPanel.jsx
        └── services/
            └── api.js          # Axios API (single source of truth)
```
