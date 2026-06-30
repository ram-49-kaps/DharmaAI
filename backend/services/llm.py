"""
LLM provider for Prakarna AI.

Primary: Llama 3.3 70B via Groq
Fallback: Groq Llama 3.1 8B, Gemma2 9B (auto-fallback on rate-limit errors)
"""

import os
import logging
import json
from functools import lru_cache

from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Define available models
MODELS = {
    "llama-3.3-70b-versatile": {"name": "Llama 3.3 70B", "context": 128000},
    "llama-3.1-8b-instant": {"name": "Llama 3.1 8B", "context": 128000},
    "gemma2-9b-it": {"name": "Gemma2 9B", "context": 8192},
    "mixtral-8x7b-32768": {"name": "Mixtral 8x7B", "context": 32768},
}

FALLBACK_SEQUENCE = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "gemma2-9b-it",
    "mixtral-8x7b-32768"
]


@lru_cache(maxsize=4)
def get_llm(model_id: str = None):
    """
    Returns the requested LLM.
    """
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key or groq_key == "your_groq_api_key_here":
        raise RuntimeError("GROQ_API_KEY not set. Please add it to your .env file.")
    
    selected_model = model_id if model_id and model_id in MODELS else "llama-3.3-70b-versatile"
    
    logger.info(f"[LLM] Initializing Groq model: {selected_model}")
    return ChatGroq(
        model=selected_model,
        temperature=0.3,
        max_tokens=4096,
        groq_api_key=groq_key,
        max_retries=0, # We handle retries/fallbacks manually
    )


@lru_cache(maxsize=1)
def get_fast_llm():
    """
    Returns a fast, lightweight LLM (Llama 3 8B).
    Used for routing and intent detection.
    """
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        return get_llm()
    
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


def _is_rate_limit(exception: Exception) -> bool:
    """Check if the exception is a rate limit error (429)."""
    error_str = str(exception).lower()
    return "429" in error_str or "rate limit" in error_str or "too many requests" in error_str


def invoke_with_fallback(chain_builder, inputs: dict, stream: bool = False, model_id: str = None):
    """Run the reasoning chain with auto-fallback on rate limits."""
    # Determine the fallback sequence starting with the requested model
    requested_model = model_id if model_id and model_id in MODELS else "llama-3.3-70b-versatile"
    
    sequence = [requested_model]
    for m in FALLBACK_SEQUENCE:
        if m not in sequence:
            sequence.append(m)
            
    if stream:
        return _stream_with_fallback(chain_builder, inputs, sequence)
    else:
        return _invoke_with_fallback_sync(chain_builder, inputs, sequence)


def _stream_with_fallback(chain_builder, inputs: dict, sequence: list):
    """Generator that catches rate limits during streaming and seamlessly falls back."""
    for i, model_name in enumerate(sequence):
        try:
            llm = get_llm(model_name)
            chain = chain_builder(llm)
            
            # If we fell back, yield a special marker event for the frontend
            if i > 0:
                logger.warning(f"[LLM] Yielding fallback info event for {model_name}")
                yield {"__fallback__": model_name, "__name__": MODELS[model_name]["name"]}
                
            # Iterate through the stream. If rate limit hits during stream setup
            # or the first token, the exception will be caught.
            for chunk in chain.stream(inputs):
                yield chunk
            return # Success!
            
        except Exception as e:
            if _is_rate_limit(e):
                logger.warning(f"[LLM] Rate limit hit on {model_name}. Attempting fallback...")
                if i < len(sequence) - 1:
                    continue # Try the next model
            # If it's not a rate limit, or we're out of models, raise the exception
            logger.error(f"[LLM] Exhausted fallbacks or unhandled error on {model_name}: {e}")
            raise e


def _invoke_with_fallback_sync(chain_builder, inputs: dict, sequence: list):
    """Synchronous invocation with rate limit fallback."""
    for i, model_name in enumerate(sequence):
        try:
            llm = get_llm(model_name)
            chain = chain_builder(llm)
            return chain.invoke(inputs)
        except Exception as e:
            if _is_rate_limit(e) and i < len(sequence) - 1:
                logger.warning(f"[LLM] Rate limit hit on {model_name}. Falling back...")
                continue
            raise e

