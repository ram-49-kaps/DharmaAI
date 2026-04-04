import os
from functools import lru_cache
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

@lru_cache(maxsize=1)
def get_llm():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set in environment / .env file")
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        max_tokens=1024,
        groq_api_key=api_key,
    )
