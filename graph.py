# if type hint not define till now but becuse we import annotations we not get any error 
from __future__ import annotations
import os
import asyncio
from contextlib import AbstractAsyncContextManager

# BaseCheckpointerSaver is a type hint .. in more upgradtion our checkpointer easly accecpt the other saver also
from langgraph.checkpoint.base import BaseCheckpointSaver
# use AsyncPostgresSaver instead of RedisSaver 
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import START, StateGraph

from agent import agent
from decide import decide_store_or_not
from reterival import retrieval_memory
from state import AgentState

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")

_resource_lock = asyncio.Lock()
_checkpointer_context: AbstractAsyncContextManager[AsyncPostgresSaver] | None = None
_checkpointer: AsyncPostgresSaver | None = None
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
            _checkpointer_context = AsyncPostgresSaver.from_conn_string(DATABASE_URL)
            _checkpointer = await _checkpointer_context.__aenter__()
            
            # Initialize LangGraph checkpoint tables schema
            await _checkpointer.asetup()

        if _workflow is None:
            _workflow = build_workflow(_checkpointer)


async def get_checkpointer() -> AsyncPostgresSaver:
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
