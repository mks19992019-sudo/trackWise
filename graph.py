from __future__ import annotations
import asyncio
from contextlib import AbstractAsyncContextManager

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.redis import AsyncRedisSaver
from langgraph.graph import START, StateGraph

from agent import agent
from decide import decide_store_or_not
from reterival import retrieval_memory
from state import AgentState

REDIS_URL = "redis://localhost:6379"

_resource_lock = asyncio.Lock()
_checkpointer_context: AbstractAsyncContextManager[AsyncRedisSaver] | None = None
_checkpointer: AsyncRedisSaver | None = None
_workflow = None


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("retrieval_memory", retrieval_memory)
    graph.add_node("store_memory", decide_store_or_not)
    graph.add_node("ai_agent", agent)

    graph.add_edge(START, "retrieval_memory")
    graph.add_edge("retrieval_memory", "store_memory")
    graph.add_edge("store_memory", "ai_agent")

    return graph


def build_workflow(checkpointer: BaseCheckpointSaver):
    return build_graph().compile(checkpointer=checkpointer)


async def _initialize_resources() -> None:
    global _checkpointer_context, _checkpointer, _workflow

    if _checkpointer is not None and _workflow is not None:
        return

    async with _resource_lock:
        if _checkpointer is None:
            _checkpointer_context = AsyncRedisSaver.from_conn_string(REDIS_URL)
            _checkpointer = await _checkpointer_context.__aenter__()

        if _workflow is None:
            _workflow = build_workflow(_checkpointer)


async def get_checkpointer() -> AsyncRedisSaver:
    await _initialize_resources()

    assert _checkpointer is not None
    return _checkpointer


async def get_workflow():
    await _initialize_resources()

    assert _workflow is not None
    return _workflow


async def close_graph_resources() -> None:
    global _checkpointer_context, _checkpointer, _workflow

    async with _resource_lock:
        if _checkpointer_context is not None:
            await _checkpointer_context.__aexit__(None, None, None)

        _checkpointer_context = None
        _checkpointer = None
        _workflow = None
