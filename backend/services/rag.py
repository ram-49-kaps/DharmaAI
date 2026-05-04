import os
import shutil
from functools import lru_cache
from typing import List

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from db.database import get_connection
from models.schemas import Source

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "../db/chroma_db")
DOCS_PATH  = os.path.join(os.path.dirname(__file__), "../data/legal_docs.txt")


def _get_embeddings():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def _build_documents_from_db() -> List[Document]:
    docs = []
    conn = get_connection()
    cur  = conn.cursor()

    for row in cur.execute("SELECT title, citation, snippet FROM cases").fetchall():
        docs.append(Document(
            page_content=f"{row['title']}\n{row['snippet']}",
            metadata={"title": row["title"], "citation": row["citation"], "type": "case"}
        ))

    for row in cur.execute("SELECT title, citation, snippet FROM statutes").fetchall():
        docs.append(Document(
            page_content=f"{row['title']}\n{row['snippet']}",
            metadata={"title": row["title"], "citation": row["citation"], "type": "statute"}
        ))

    for row in cur.execute("SELECT term, definition FROM glossary").fetchall():
        docs.append(Document(
            page_content=f"{row['term']}: {row['definition']}",
            metadata={"title": row["term"], "citation": "Legal Glossary", "type": "glossary"}
        ))

    conn.close()
    return docs


def _build_documents_from_file() -> List[Document]:
    if not os.path.exists(DOCS_PATH):
        return []
    with open(DOCS_PATH, "r", encoding="utf-8") as f:
        raw = f.read()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600, chunk_overlap=80,
        separators=["\n\nDOCUMENT:", "\n\n", "\n", " "]
    )
    chunks = splitter.split_text(raw)
    return [
        Document(page_content=chunk, metadata={"title": "Legal Document", "citation": "", "type": "statute"})
        for chunk in chunks
    ]


def build_vector_store() -> Chroma:
    print("[RAG] Building Chroma index …")
    
    # Clear old chroma db if exists to prevent duplicates
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)

    embeddings = _get_embeddings()
    db_docs    = _build_documents_from_db()
    file_docs  = _build_documents_from_file()
    all_docs   = db_docs + file_docs

    if not all_docs:
        raise RuntimeError("No documents to embed. Run seed.py first.")

    store = Chroma.from_documents(
        documents=all_docs, 
        embedding=embeddings, 
        persist_directory=CHROMA_PATH
    )
    print(f"[RAG] Indexed {len(all_docs)} documents → {CHROMA_PATH}")
    return store


@lru_cache(maxsize=1)
def get_vector_store() -> Chroma:
    embeddings = _get_embeddings()
    if os.path.exists(CHROMA_PATH) and os.listdir(CHROMA_PATH):
        print("[RAG] Loading cached Chroma index …")
        return Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
    return build_vector_store()


def retrieve_sources(query: str, k: int = 4) -> List[Source]:
    store = get_vector_store()
    hits  = store.similarity_search(query, k=k)
    seen, sources = set(), []
    for doc in hits:
        key = doc.metadata.get("title", "")
        if key in seen:
            continue
        seen.add(key)
        sources.append(Source(
            title    = doc.metadata.get("title", "Legal Document"),
            type     = doc.metadata.get("type", "statute"),
            citation = doc.metadata.get("citation", ""),
        ))
    return sources


def retrieve_context(query: str, k: int = 4) -> str:
    store = get_vector_store()
    hits  = store.similarity_search(query, k=k)
    return "\n\n".join(doc.page_content for doc in hits)
