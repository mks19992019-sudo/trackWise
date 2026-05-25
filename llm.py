from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

DEFAULT_AGENT_MODEL = os.getenv("GROQ_AGENT_MODEL", "llama-3.3-70b-versatile")
DEFAULT_MEMORY_MODEL = os.getenv("GROQ_MEMORY_MODEL", "llama-3.1-8b-instant")
DEFAULT_TEMPERATURE = float(os.getenv("GROQ_TEMPERATURE", "0"))

model2 = ChatGroq(
    model=DEFAULT_AGENT_MODEL,
    temperature=DEFAULT_TEMPERATURE,
)

classification_model2 = ChatGroq(
    model=DEFAULT_MEMORY_MODEL,
    temperature=0,
)

GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
DEFAULT_GOOGLE_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

model = ChatGoogleGenerativeAI(
    model=DEFAULT_GOOGLE_MODEL,
    api_key=GOOGLE_API_KEY,
    temperature=0,
)
classification_model = ChatGoogleGenerativeAI(
    model=DEFAULT_GOOGLE_MODEL,
    api_key=GOOGLE_API_KEY,
    temperature=0,
)
