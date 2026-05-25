from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, ConfigDict, StringConstraints
from redis.asyncio import Redis

from database import close_db_pool, initialize_database
from graph import close_graph_resources, get_checkpointer, get_workflow
from dotenv import load_dotenv

load_dotenv()

SESSION_TTL_SECONDS = 20
TrimmedText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

Redis_client = Redis(
    host="localhost",
    port=6379,
    decode_responses=True,
)


class ChatMessage(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    message: TrimmedText
    thread_id: TrimmedText





@asynccontextmanager
async def lifespan(_: FastAPI):
    # start server
    await initialize_database()

    try:
        yield
    finally:
        # shutdown the server
        await Redis_client.aclose()
        await close_graph_resources()
        await close_db_pool()


app = FastAPI(
    title="Finance AI System",
    description="AI-powered personal finance management",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# AGENTIC ENDPOINTS (Main Focus)
# ============================================================================

@app.get("/")
async def home():
    """Health check endpoint"""
    return {"message": "Finance AI System is running"}


@app.post("/chat")
async def chat(payload: ChatMessage):
    """Main chat endpoint - AI agent processes user messages"""
    thread_id = payload.thread_id
    user_message = payload.message
    session_key = f"session:{thread_id}"
    
    if not await Redis_client.exists(session_key):
        checkpointer = await get_checkpointer()
        await checkpointer.adelete_thread(thread_id)

    await Redis_client.set(session_key, "active", ex=SESSION_TTL_SECONDS)

    workflow = await get_workflow()
    result = await workflow.ainvoke(
        {
            "messages": [HumanMessage(content=user_message)],
            "thread_id": thread_id,
        },
        {"configurable": {"thread_id": thread_id}},
    )

    response_messages = result.get("messages", [])

    if not response_messages:
        raise HTTPException(status_code=500, detail="Workflow returned no messages.")

    return response_messages[-1].content



