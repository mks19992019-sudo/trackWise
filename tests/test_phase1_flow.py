import asyncio
from pathlib import Path
import sys

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import agent as agent_module
import decide as decide_module
import graph as graph_module
import main as main_module
import reterival as retrieval_module


def test_agent_returns_only_the_latest_assistant_message(monkeypatch) -> None:
    class FakeExpenseAgent:
        def __init__(self) -> None:
            self.payload = None

        async def ainvoke(self, payload):
            self.payload = payload
            return {
                "messages": payload["messages"]
                + [AIMessage(content="Budget looks good.")],
            }

    fake_agent = FakeExpenseAgent()

    async def fake_get_expense_agent():
        return fake_agent

    monkeypatch.setattr(agent_module, "aget_expense_agent", fake_get_expense_agent)

    result = asyncio.run(
        agent_module.agent(
            {
                "messages": [HumanMessage(content="How much did I spend?")],
                "thread_id": "user-1",
                "retrieved_memories": "User tracks expenses in USD.",
            }
        )
    )

    assert len(result["messages"]) == 1
    assert result["messages"][0].content == "Budget looks good."
    system_messages = [
        message
        for message in fake_agent.payload["messages"]
        if isinstance(message, SystemMessage)
    ]
    assert any("user_scope: user-1" in message.content for message in system_messages)
    assert any("USD" in message.content for message in system_messages)


def test_retrieval_memory_falls_back_when_vector_search_fails(monkeypatch) -> None:
    class FailingVectorStore:
        async def asimilarity_search(self, *args, **kwargs):
            raise RuntimeError("qdrant is unavailable")

    async def fake_get_vector_store():
        return FailingVectorStore()

    monkeypatch.setattr(retrieval_module, "aget_vector_store", fake_get_vector_store)

    result = asyncio.run(
        retrieval_module.retrieval_memory(
            {
                "messages": [HumanMessage(content="Remember my preferred currency")],
                "thread_id": "user-1",
            },
            {"configurable": {"thread_id": "user-1"}},
        )
    )

    assert result == {"retrieved_memories": retrieval_module.NO_RELEVANT_MEMORIES}


def test_retrieval_memory_enriches_state_with_search_results(monkeypatch) -> None:
    class FakeVectorStore:
        async def asimilarity_search(self, query: str, k: int = 10):
            if query == "currency" and k == 10:
                return [
                    type("obj", (object,), {"page_content": "User prefers CAD"})(),
                ]
            return []

    async def fake_get_vector_store():
        return FakeVectorStore()

    monkeypatch.setattr(retrieval_module, "aget_vector_store", fake_get_vector_store)

    result = asyncio.run(
        retrieval_module.retrieval_memory(
            {
                "messages": [HumanMessage(content="What currency do I use?")],
                "thread_id": "user-1",
            },
            {"configurable": {"thread_id": "user-1"}},
        )
    )

    assert result == {"retrieved_memories": "User prefers CAD"}


def test_decide_store_or_not_returns_state_unchanged_when_no_system_message(
    monkeypatch,
) -> None:
    result = asyncio.run(
        decide_module.decide_store_or_not(
            {
                "messages": [HumanMessage(content="How much did I spend?")],
                "thread_id": "user-1",
                "retrieved_memories": "User tracks expenses in USD.",
            }
        )
    )

    assert result == {
        "messages": [HumanMessage(content="How much did I spend?")],
        "thread_id": "user-1",
        "retrieved_memories": "User tracks expenses in USD.",
    }


def test_workflow_maintains_state_across_invocations(monkeypatch) -> None:
    async def fake_agent(state):
        return {"messages": state["messages"] + [AIMessage(content="reply to show me my summary")]}

    async def fake_decide_store_or_not(state, config=None):
        return state

    async def fake_retrieval_memory(state, config=None):
        thread_id = state.get("thread_id", "")
        return {"retrieved_memories": f"memory for {thread_id}"}

    monkeypatch.setattr(agent_module, "agent", fake_agent)
    monkeypatch.setattr(decide_module, "decide_store_or_not", fake_decide_store_or_not)
    monkeypatch.setattr(retrieval_module, "retrieval_memory", fake_retrieval_memory)

    workflow = graph_module.build_workflow(InMemorySaver())
    config = {"configurable": {"thread_id": "thread-1"}}

    first_result = asyncio.run(
        workflow.ainvoke(
            {
                "messages": [HumanMessage(content="hello")],
                "thread_id": "thread-1",
            },
            config,
        )
    )
    second_result = asyncio.run(
        workflow.ainvoke(
            {
                "messages": [HumanMessage(content="show me my summary")],
                "thread_id": "thread-1",
            },
            config,
        )
    )
    state = workflow.get_state(config).values

    assert first_result["messages"][-1].content == "reply to show me my summary"
    assert second_result["messages"][-1].content == "reply to show me my summary"
    assert [message.content for message in state["messages"]] == [
        "hello",
        "reply to show me my summary",
        "show me my summary",
        "reply to show me my summary",
    ]
    assert state["thread_id"] == "thread-1"
    assert state["retrieved_memories"] == "memory for thread-1"


def test_chat_endpoint_keeps_existing_contract(monkeypatch) -> None:
    class FakeWorkflow:
        async def ainvoke(self, payload, config):
            assert payload["thread_id"] == "user-1"
            assert payload["messages"][0].content == "Track lunch expense"
            assert config["configurable"]["thread_id"] == "user-1"
            return {"messages": [AIMessage(content="Done.")]}

    fake_workflow = FakeWorkflow()

    async def fake_get_workflow():
        return fake_workflow

    async def fake_close_graph_resources() -> None:
        return None

    async def fake_initialize_database():
        return None

    async def fake_close_db_pool() -> None:
        return None

    async def fake_update_thread_activity(thread_id: str) -> None:
        return None

    monkeypatch.setattr(main_module, "get_workflow", fake_get_workflow)
    monkeypatch.setattr(main_module, "close_graph_resources", fake_close_graph_resources)
    monkeypatch.setattr(main_module, "initialize_database", fake_initialize_database)
    monkeypatch.setattr(main_module, "close_db_pool", fake_close_db_pool)
    monkeypatch.setattr(main_module, "update_thread_activity", fake_update_thread_activity)

    with TestClient(main_module.app) as client:
        response = client.post(
            "/chat",
            json={
                "message": "  Track lunch expense  ",
                "thread_id": "  user-1  ",
            },
        )

    assert response.status_code == 200
    assert response.json() == "Done."
