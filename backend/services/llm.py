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


@lru_cache(maxsize=1)
def get_fast_llm():
    """
    Returns a fast, lightweight LLM (Llama 3 8B).
    Used for routing and intent detection to save the 70B quota for reasoning.
    """
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        return get_llm() # Fallback to primary
    
    return ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0.1,
        groq_api_key=groq_key,
        max_retries=3,
    )


def invoke_fast(chain_builder, inputs: dict) -> str:
    """Run a chain using the high-limit 8B model."""
    llm = get_fast_llm()
    chain = chain_builder(llm)
    return chain.invoke(inputs)


def invoke_with_fallback(chain_builder, inputs: dict) -> str:
    """Run the reasoning chain using the 70B model."""
    llm = get_llm()
    chain = chain_builder(llm)
    return chain.invoke(inputs)

