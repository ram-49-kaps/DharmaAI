"""
RAG-first retrieval engine for DharmaAI v2.

Every query goes through this engine before reaching the LLM.
Uses Gemini text-embedding-004 for embeddings and ChromaDB for storage.
"""

from __future__ import annotations

import logging
import os
from typing import List, Optional

from google import genai
import chromadb
from chromadb.utils import embedding_functions
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "../db/chroma_db_v2")

COLLECTIONS = ["iks_texts", "modern_law", "case_law", "glossary"]

EMBED_MODEL = "text-embedding-004"


class GeminiEmbeddingFunction(embedding_functions.EmbeddingFunction):
    """ChromaDB-compatible wrapper for Gemini text-embedding-004."""

    def __init__(self, api_key: str):
        self._client = genai.Client(api_key=api_key)

    def __call__(self, input: List[str]) -> List[List[float]]:
        """Batch-embed all texts in a single API call to conserve quota."""
        if not input:
            return []
        try:
            resp = self._client.models.embed_content(
                model=EMBED_MODEL,
                contents=input,
            )
            return [e.values for e in resp.embeddings]
        except Exception as exc:
            logger.error(f"[Embed] Batch embedding failed: {exc}")
            # Fallback: return zero vectors so the app doesn't crash
            return [[0.0] * 768 for _ in input]


def _get_embedding_fn() -> GeminiEmbeddingFunction:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set — required for RAG embeddings")
    return GeminiEmbeddingFunction(api_key=api_key)


def _embed_query(query: str) -> List[float]:
    """Embed a single query string for retrieval."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    client = genai.Client(api_key=api_key)
    resp = client.models.embed_content(
        model=EMBED_MODEL,
        contents=query,
    )
    return resp.embeddings[0].values


class RAGEngine:
    """
    RAG-first retrieval pipeline.

    Flow: embed_query → hybrid_search (all collections) → rerank → build_context
    """

    def __init__(self):
        self._client: Optional[chromadb.PersistentClient] = None
        self._embed_fn: Optional[GeminiEmbeddingFunction] = None
        self._collections: dict = {}

    def _ensure_init(self):
        if self._client is not None:
            return
        os.makedirs(CHROMA_PATH, exist_ok=True)
        self._client = chromadb.PersistentClient(path=CHROMA_PATH)
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            self._embed_fn = _get_embedding_fn()
        else:
            # Fall back to sentence-transformers if no Gemini key
            from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
            self._embed_fn = SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
            logger.warning("[RAG] Using fallback sentence-transformer embeddings")

        for name in COLLECTIONS:
            try:
                self._collections[name] = self._client.get_or_create_collection(
                    name=name,
                    embedding_function=self._embed_fn,
                    metadata={"hnsw:space": "cosine"},
                )
            except Exception as exc:
                logger.error(f"[RAG] Failed to init collection '{name}': {exc}")

    def embed_query(self, query: str) -> List[float]:
        """Embed a query using Gemini text-embedding-004."""
        try:
            return _embed_query(query)
        except Exception as exc:
            logger.error(f"[RAG] embed_query failed: {exc}")
            return []

    def hybrid_search(self, query: str, k: int = 10) -> List[dict]:
        """
        Search all collections and return top-k results by similarity.
        Returns list of dicts with keys: content, metadata, score, collection.
        """
        self._ensure_init()
        all_results: List[dict] = []

        for col_name, collection in self._collections.items():
            try:
                count = collection.count()
                if count == 0:
                    continue
                n_results = min(k, count)
                results = collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    include=["documents", "metadatas", "distances"],
                )
                docs = results.get("documents", [[]])[0]
                metas = results.get("metadatas", [[]])[0]
                dists = results.get("distances", [[]])[0]

                for doc, meta, dist in zip(docs, metas, dists):
                    # Convert cosine distance to similarity score
                    score = 1.0 - dist
                    all_results.append({
                        "content": doc,
                        "metadata": meta or {},
                        "score": score,
                        "collection": col_name,
                    })
            except Exception as exc:
                logger.error(f"[RAG] Search error in '{col_name}': {exc}")

        # Sort by score descending
        all_results.sort(key=lambda x: x["score"], reverse=True)
        return all_results[:k]

    def rerank(self, results: List[dict], query: str, k: int = 5) -> List[dict]:
        """
        Simple reranking: boost results whose metadata matches query tokens.
        A cross-encoder model can replace this for production.
        """
        query_lower = query.lower()
        query_tokens = set(query_lower.split())

        for r in results:
            meta = r.get("metadata", {})
            title = str(meta.get("title", "")).lower()
            section = str(meta.get("section", "")).lower()
            boost = 0.0
            for token in query_tokens:
                if len(token) > 3 and (token in title or token in section):
                    boost += 0.05
            r["score"] += boost

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:k]

    def build_context(self, results: List[dict]) -> str:
        """
        Format retrieval results as structured context with citation tags.
        Format: [Source: <collection> | <title> | <section> | <page>]
        """
        if not results:
            return "No relevant sources found in the knowledge base."

        parts = []
        for i, r in enumerate(results, 1):
            meta = r.get("metadata", {})
            col = r.get("collection", "unknown")
            title = meta.get("title", "Unknown Source")
            section = meta.get("section", "")
            page = meta.get("page", "")
            citation = meta.get("citation", "")

            # Build citation tag
            cite_parts = [col.replace("_", " ").title(), title]
            if section:
                cite_parts.append(section)
            if page:
                cite_parts.append(f"p.{page}")
            elif citation:
                cite_parts.append(citation)
            cite_tag = f"[Source: {' | '.join(cite_parts)}]"

            parts.append(f"{cite_tag}\n{r['content']}")

        return "\n\n---\n\n".join(parts)

    def retrieve(self, query: str, k_initial: int = 10, k_final: int = 5) -> tuple[str, List[dict]]:
        """
        Full retrieval pipeline: search → rerank → build context.
        Returns (context_string, raw_results).
        """
        results = self.hybrid_search(query, k=k_initial)
        if not results:
            return "No relevant sources found in the knowledge base.", []
        reranked = self.rerank(results, query, k=k_final)
        context = self.build_context(reranked)
        return context, reranked

    def add_documents(
        self,
        documents: List[str],
        metadatas: List[dict],
        ids: List[str],
        collection_name: str,
    ) -> int:
        """Add documents to a named collection. Returns count added."""
        self._ensure_init()
        if collection_name not in self._collections:
            raise ValueError(
                f"Unknown collection '{collection_name}'. "
                f"Must be one of: {COLLECTIONS}"
            )
        collection = self._collections[collection_name]
        collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
        return len(documents)

    def collection_count(self, collection_name: str) -> int:
        """Return number of documents in a collection."""
        self._ensure_init()
        col = self._collections.get(collection_name)
        return col.count() if col else 0


# ── Singleton ─────────────────────────────────────────────────────────────────

_rag_engine: Optional[RAGEngine] = None


def get_rag_engine() -> RAGEngine:
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine()
    return _rag_engine
