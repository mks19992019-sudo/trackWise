from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq


load_dotenv()

DEFAULT_AGENT_MODEL = os.getenv("GROQ_AGENT_MODEL", "llama-3.3-70b-versatile")
DEFAULT_MEMORY_MODEL = os.getenv("GROQ_MEMORY_MODEL", "llama-3.1-8b-instant")
DEFAULT_TEMPERATURE = float(os.getenv("GROQ_TEMPERATURE", "0"))

model = ChatGroq(
    model=DEFAULT_AGENT_MODEL,
    temperature=DEFAULT_TEMPERATURE,
)

classification_model = ChatGroq(
    model=DEFAULT_MEMORY_MODEL,
    temperature=0,
)





