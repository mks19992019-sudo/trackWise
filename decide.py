from __future__ import annotations

import asyncio
import logging

from langchain_core.messages import BaseMessage, HumanMessage
from pydantic import BaseModel

from embeding import aget_vector_store
from llm import model
from prompts import prompt1, prompt2
from reterival import NO_RELEVANT_MEMORIES
from state import AgentState

logger = logging.getLogger(__name__)


class StoreDecision(BaseModel):
    """Determine whether to store the user query in long-term memory."""

    ans: bool


structured_model = model.with_structured_output(StoreDecision)
should_store_chain = prompt1 | structured_model
is_new_memory_chain = prompt2 | structured_model


def _message_text(message: BaseMessage) -> str:
    content = message.content

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []

        for block in content:
            if isinstance(block, str):
                parts.append(block)
                continue

            if isinstance(block, dict):
                text = block.get("text")
                if isinstance(text, str):
                    parts.append(text)

        return "\n".join(part for part in parts if part).strip()

    return str(content)


def _latest_user_message(state: AgentState) -> str:
    for message in reversed(state["messages"]):
        if isinstance(message, HumanMessage):
            text = _message_text(message).strip()
            if text:
                return text

    raise ValueError("No user message found in the workflow state.")


async def _should_store(query: str) -> bool:
    result = await should_store_chain.ainvoke({"query": query})
    return result.ans


async def _contains_new_information(query: str, memories: str) -> bool:
    if not memories or memories == NO_RELEVANT_MEMORIES:
        return True

    result = await is_new_memory_chain.ainvoke(
        {"query": query, "memories": memories}
    )
    return result.ans


async def _store_memory(query: str, thread_id: str) -> None:
    vector_store = await aget_vector_store()

    if hasattr(vector_store, "aadd_texts"):
        await vector_store.aadd_texts(
            texts=[query],
            metadatas=[{"user_id": thread_id}],
        )
        return

    await asyncio.to_thread(
        vector_store.add_texts,
        texts=[query],
        metadatas=[{"user_id": thread_id}],
    )


async def decide_store_or_not(state: AgentState) -> dict[str, str]:
    query = _latest_user_message(state)
    thread_id = state["thread_id"]
    memories = state.get("retrieved_memories", NO_RELEVANT_MEMORIES)

    try:
        if not await _should_store(query):
            return {}

        if not await _contains_new_information(query, memories):
            return {}

        await _store_memory(query, thread_id)
    except Exception:
        logger.exception("Long-term memory storage failed for thread_id=%s", thread_id)

    return {}
