"""
LLM provider for DharmaAI.

Primary: Gemini 2.0 Flash via google-generativeai
Fallback: Groq Llama 3.3 (auto-fallback on rate-limit errors)
"""

import os
import logging
from functools import lru_cache

from google import genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_llm():
    """
    Returns the primary LLM (Groq Llama 3.3).
    We use Groq for generation because it is fast and free.
    Local embeddings are now used to eliminate Gemini rate limits.
    """
    return _get_groq_llm()


@lru_cache(maxsize=1)
def _get_groq_llm():
    """Returns the Groq LLM (Llama 3.3 70B)."""
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key or groq_key == "your_groq_api_key_here":
        raise RuntimeError("GROQ_API_KEY not set. Please add it to your .env file.")
    
    logger.info("[LLM] Using Groq Llama 3.3 for generation")
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        max_tokens=4096,
        groq_api_key=groq_key,
        max_retries=3,
    )


def invoke_with_fallback(chain_builder, inputs: dict) -> str:
    """
    Run the chain using Groq.
    """
    llm = get_llm()
    chain = chain_builder(llm)
    return chain.invoke(inputs)


def get_gemini_client() -> genai.Client:
    """Direct Gemini client — kept only as a backup for non-critical tasks."""
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    return genai.Client(api_key=gemini_key)

