"""
URL ingestion pipeline for DharmaAI v2.
Uses trafilatura for high-quality main text extraction.
"""

import hashlib
import logging
from typing import List, Tuple

from services.rag_engine import get_rag_engine

logger = logging.getLogger(__name__)

class URLIngestor:
    """
    Extracts content from a URL and stores it in ChromaDB.
    """

    def extract_content(self, url: str) -> str:
        """
        Download and extract the main content from the URL.
        """
        import trafilatura

        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            raise ValueError(f"Failed to fetch content from URL: {url}")
        
        # Extract main text
        content = trafilatura.extract(downloaded, include_comments=False, include_tables=True)
        if not content:
            raise ValueError(f"No meaningful text could be extracted from {url}")
        
        return content

    def simple_chunk(self, text: str, max_chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Simple character-based chunking since web pages don't have page numbers.
        """
        chunks = []
        start = 0
        while start < len(text):
            end = start + max_chunk_size
            chunk = text[start:end]
            chunks.append(chunk.strip())
            start += (max_chunk_size - overlap)
        return chunks

    def ingest(self, url: str, category: str) -> int:
        """
        Full pipeline: fetch -> extract -> chunk -> store.
        """
        logger.info(f"[URL] Ingesting: {url}")
        
        text = self.extract_content(url)
        chunks = self.simple_chunk(text)
        
        # Use filename-like identifier from URL
        filename = url.split("/")[-1] or "web_page"
        if not filename.isalnum():
            filename = hashlib.md5(url.encode()).hexdigest()[:10]

        engine = get_rag_engine()
        
        category_labels = {
            "iks_texts": "IKS (Web)",
            "modern_law": "Statute (Web)",
            "case_law": "Case (Web)",
        }
        source_type = category_labels.get(category, "Web Source")

        metadatas = [
            {
                "source_type": source_type,
                "category": category,
                "title": url,
                "section": f"Excerpt from {url}",
                "page": "Web",
                "filename": filename,
                "url": url
            }
            for _ in chunks
        ]

        ids = [
            f"web_{hashlib.md5((url + str(i)).encode()).hexdigest()[:12]}"
            for i, _ in enumerate(chunks)
        ]

        count = engine.add_documents(
            documents=chunks,
            metadatas=metadatas,
            ids=ids,
            collection_name=category,
        )
        
        logger.info(f"[URL] Stored {count} chunks in '{category}' from {url}")
        return count
