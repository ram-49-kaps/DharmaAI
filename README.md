# ⚖️ DharmaAI: Indian Legal Assistant

DharmaAI is an advanced, full-stack legal reasoning chatbot designed exclusively for the intricacies of Indian jurisprudence. Powered by the ultra-fast Groq API (Llama 3) and a custom Retrieval-Augmented Generation (RAG) pipeline built with ChromaDB, it instantly analyzes case laws, statutes, and ancient Indian Knowledge Systems (IKS).

Designed for legal education and legal professionals, DharmaAI bridges the gap between modern state laws and traditional Dharmic principles in a sleek, production-ready interface.

---

## ✨ Key Features
- **🔍 High-Speed RAG Pipeline:** Contextual search over the Indian Penal Code, Bhartiya Nyaya Sanhita, foundational Constitutional Law cases, and core legal texts using ChromaDB.
- **🧠 Advanced Legal Reasoning:** Built-in templates for IRAC (Issue, Rule, Application, Conclusion) and IDAR (Issue, Dharma, Application of Danda, Resolution) methodologies.
- **⚡ Intent-Based Routing:** The LangChain backend automatically detects the user's intent (Case Law, Statute Lookup, Definition, IRAC) and routes the prompt via specialized LLM chains.
- **🏺 IKS Integration:** Maps modern constitutional doctrines back to historical texts like the *Arthashastra* and *Dharmashastra*.
- **📱 Premium "Dharma Logic" UI:** A beautifully designed React frontend using Lucide icons, glass-morphism, and responsive CSS.

## 🛠️ Technology Stack
### Frontend
- **React.js & Vite:** High-performance UI rendering.
- **Vanilla CSS:** Custom design tokens mapped to the "Dharma Logic" color palette.
- **Lucide React:** Premium scalable SVG iconography.

### Backend
- **Python / FastAPI:** Lightning-fast async REST API.
- **Groq API & Llama-3.3-70b:** State-of-the-art LLM inference.
- **LangChain:** Agentic routing and prompt templating.
- **ChromaDB & SQLite:** Persistent vector storage and chat history memory.

---

## 🚀 Getting Started Locally

### 1. Clone the Repository
```bash
git clone https://github.com/ram-49-kaps/DharmaAI.git
cd DharmaAI
```

### 2. Run the Backend (FastAPI)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create a .env file and add your GROQ_API_KEY
echo "GROQ_API_KEY=your_key_here" > .env

# Run the server
uvicorn app:app --port 8000
```

### 3. Run the Frontend (React)
```bash
cd frontend
npm install
npm start
```

*The application will now be running on `http://localhost:3000`.*

---

## 👨‍💻 Created By
**Ram Kapadia** - Artificial Intelligence & Full-Stack Developer
