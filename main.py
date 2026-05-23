from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, HTTPException
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, ConfigDict, StringConstraints
from redis.asyncio import Redis

from database import close_db_pool, initialize_database
from graph import close_graph_resources, get_checkpointer, get_workflow

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
    await initialize_database()

    try:
        yield
    finally:
        await Redis_client.aclose()
        await close_graph_resources()
        await close_db_pool()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def home():
    return {"message": "fast api is working"}


@app.post("/chat")
async def chat(payload: ChatMessage):
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
