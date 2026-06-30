"""
PDF ingestion pipeline for Prakarna AI v2.

Extracts text with page numbers using pdfplumber,
chunks at section boundaries, and stores in ChromaDB.
"""

from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path
from typing import List, Tuple

import pypdf

from services.rag_engine import get_rag_engine

logger = logging.getLogger(__name__)

# Headings that signal a new section boundary for chunking
SECTION_PATTERNS = [
    r"^\s*CHAPTER\s+[IVXLCDM\d]+",
    r"^\s*Chapter\s+\d+",
    r"^\s*PART\s+[IVXLCDM\d]+",
    r"^\s*Section\s+\d+",
    r"^\s*SECTION\s+\d+",
    r"^\s*Article\s+\d+",
    r"^\s*ARTICLE\s+\d+",
    r"^\s*\d+\.\s+[A-Z]",
]
_SECTION_RE = re.compile("|".join(SECTION_PATTERNS), re.MULTILINE)


class PDFIngestor:
    """
    Ingests PDF files into ChromaDB collections with page-level metadata.

    Usage:
        ingestor = PDFIngestor()
        chunks = ingestor.ingest(pdf_path, category="iks_texts")
    """

    def extract_with_metadata(
        self, pdf_path: str
    ) -> List[Tuple[str, int]]:
        """
        Extract text page-by-page using pypdf.
        Returns list of (page_text, page_number) tuples.
        """
        pages = []
        reader = pypdf.PdfReader(pdf_path)
        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text()
            if text and text.strip():
                pages.append((text.strip(), i))
        logger.info(f"[PDF] Extracted {len(pages)} pages from {pdf_path}")
        return pages

    def section_aware_chunk(
        self,
        pages: List[Tuple[str, int]],
        max_chunk_size: int = 800,
        overlap: int = 100,
    ) -> List[Tuple[str, int, int]]:
        """
        Chunk text at section/heading boundaries.
        Returns list of (chunk_text, start_page, end_page).
        """
        chunks: List[Tuple[str, int, int]] = []
        current_chunk: List[str] = []
        current_size = 0
        start_page = pages[0][1] if pages else 1
        current_end_page = start_page

        for page_text, page_num in pages:
            lines = page_text.split("\n")
            for line in lines:
                is_section_break = bool(_SECTION_RE.match(line))

                if is_section_break and current_chunk and current_size > 200:
                    # Flush current chunk
                    chunks.append(
                        ("\n".join(current_chunk), start_page, current_end_page)
                    )
                    # Start new chunk with overlap
                    overlap_lines = current_chunk[-3:] if len(current_chunk) >= 3 else current_chunk
                    current_chunk = overlap_lines + [line]
                    current_size = sum(len(l) for l in current_chunk)
                    start_page = page_num
                else:
                    current_chunk.append(line)
                    current_size += len(line)

                if current_size >= max_chunk_size:
                    chunks.append(
                        ("\n".join(current_chunk), start_page, current_end_page)
                    )
                    overlap_lines = current_chunk[-3:] if len(current_chunk) >= 3 else current_chunk
                    current_chunk = overlap_lines
                    current_size = sum(len(l) for l in current_chunk)
                    start_page = page_num

            current_end_page = page_num

        if current_chunk:
            chunks.append(("\n".join(current_chunk), start_page, current_end_page))

        logger.info(f"[PDF] Created {len(chunks)} chunks")
        return chunks

    def tag_metadata(
        self,
        chunks: List[Tuple[str, int, int]],
        category: str,
        filename: str,
    ) -> List[dict]:
        """
        Attach metadata tags to chunks.
        category: "iks_texts" | "modern_law" | "case_law"
        """
        category_labels = {
            "iks_texts": "IKS",
            "modern_law": "Statute",
            "case_law": "Case",
            "glossary": "Glossary",
        }
        source_type = category_labels.get(category, "Unknown")

        metadatas = []
        for text, start_page, end_page in chunks:
            # Try to extract title from first meaningful line
            first_line = next(
                (l.strip() for l in text.split("\n") if len(l.strip()) > 10), filename
            )
            title = first_line[:80] if len(first_line) > 80 else first_line

            page_str = str(start_page) if start_page == end_page else f"{start_page}-{end_page}"

            metadatas.append({
                "source_type": source_type,
                "category": category,
                "title": filename,
                "section": title,
                "page": page_str,
                "filename": filename,
            })

        return metadatas

    def embed_and_store(
        self,
        chunks: List[Tuple[str, int, int]],
        metadatas: List[dict],
        collection_name: str,
        filename: str,
    ) -> int:
        """Store chunks with metadata in ChromaDB. Returns count stored."""
        engine = get_rag_engine()
        documents = [text for text, _, _ in chunks]

        # Generate stable IDs based on content hash + index to guarantee uniqueness
        ids = [
            f"{filename}_{i}_{hashlib.md5(doc.encode()).hexdigest()[:12]}"
            for i, doc in enumerate(documents)
        ]

        count = engine.add_documents(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
            collection_name=collection_name,
        )
        logger.info(f"[PDF] Stored {count} chunks in '{collection_name}'")
        return count

    def ingest(self, pdf_path: str, category: str, original_filename: str = None) -> int:
        """
        Full ingestion pipeline: extract → chunk → tag → store.
        Returns number of chunks stored.
        """
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        filename = Path(original_filename).stem if original_filename else path.stem
        pages = self.extract_with_metadata(str(path))

        if not pages:
            raise ValueError(f"No text extracted from {pdf_path}. Is it a scanned PDF?")

        chunks = self.section_aware_chunk(pages)
        metadatas = self.tag_metadata(chunks, category, filename)
        count = self.embed_and_store(chunks, metadatas, category, filename)
        return count
