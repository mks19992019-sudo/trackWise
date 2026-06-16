from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from .settings import settings


load_dotenv()


model = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=settings.GROQ_API_KEY,
)





'''
classification_model = ChatGroq(
    model=DEFAULT_MEMORY_MODEL,
    temperature=0,
)
'''