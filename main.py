from __future__ import annotations


import asyncio
from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, ConfigDict, StringConstraints

from database import close_db_pool, initialize_database, cleanup_old_checkpoints, update_thread_activity
from graph import close_graph_resources, get_workflow
from dotenv import load_dotenv

load_dotenv()

TrimmedText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

_cleanup_task: asyncio.Task | None = None


async def cleanup_scheduler():
    """Run cleanup every 24 hours"""
    while True:
        try:
            await asyncio.sleep(86400)  # 24 hours
            await cleanup_old_checkpoints()
        except Exception:
            pass


class ChatMessage(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    message: TrimmedText
    thread_id: TrimmedText


@asynccontextmanager
async def lifespan(_: FastAPI):
    # start server
    global _cleanup_task
    await initialize_database()
    _cleanup_task = asyncio.create_task(cleanup_scheduler())

    try:
        yield
    finally:
        # shutdown the server
        if _cleanup_task:
            _cleanup_task.cancel()
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


@app.get("/")
async def home():
    """Health check endpoint"""
    return {"message": "Finance AI System is running"}


@app.post("/chat")
async def chat(payload: ChatMessage):
    """Main chat endpoint - AI agent processes user messages"""
    thread_id = payload.thread_id
    user_message = payload.message
    
    # Update activity timestamp for this thread
    await update_thread_activity(thread_id)

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
