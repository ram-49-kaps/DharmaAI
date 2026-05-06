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
    Gemini is only used for embeddings to save RAM.
    """
    groq_llm = _get_groq_llm()
    if groq_llm:
        return groq_llm
    
    # Absolute fallback if Groq is missing
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        logger.info("[LLM] Groq missing, using Gemini 2.0 Flash")
        return ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=gemini_key,
            temperature=0.3,
            max_output_tokens=4096,
            max_retries=0,
        )
    raise RuntimeError("No LLM configured. Please set GROQ_API_KEY.")


@lru_cache(maxsize=1)
def _get_groq_llm():
    """Returns the Groq LLM (Llama 3.3 70B)."""
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key or groq_key == "your_groq_api_key_here":
        return None
    logger.info("[LLM] Groq Llama 3.3 available as fallback")
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        max_tokens=4096,
        groq_api_key=groq_key,
        max_retries=0,
    )


def get_fallback_llm():
    """Returns Gemini LLM for use as a fallback, or None if unavailable."""
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        return ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=gemini_key,
            temperature=0.3,
            max_output_tokens=4096,
            max_retries=0,
        )
    return None


def invoke_with_fallback(chain_builder, inputs: dict) -> str:
    """
    Try primary LLM (Gemini); if it fails with rate-limit, retry with Groq.

    chain_builder: a function that takes an LLM and returns a runnable chain.
    inputs: dict to pass to chain.invoke().
    """
    primary = get_llm()
    try:
        chain = chain_builder(primary)
        return chain.invoke(inputs)
    except Exception as exc:
        exc_str = str(exc)
        if "429" in exc_str or "RESOURCE_EXHAUSTED" in exc_str:
            fallback = get_fallback_llm()
            if fallback:
                logger.warning("[LLM] Groq rate-limited — falling back to Gemini")
                chain = chain_builder(fallback)
                return chain.invoke(inputs)
            else:
                logger.error("[LLM] Groq rate-limited and no Gemini key configured")
        raise


def get_gemini_client() -> genai.Client:
    """Direct Gemini client for embeddings and non-LangChain usage."""
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    return genai.Client(api_key=gemini_key)

