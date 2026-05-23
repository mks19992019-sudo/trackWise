import logging

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from qdrant_client.models import FieldCondition, Filter, MatchValue

from embeding import aget_vector_store
from state import AgentState

logger = logging.getLogger(__name__)
NO_RELEVANT_MEMORIES = "No relevant memories."


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


def _resolve_thread_id(
    state: AgentState,
    config: RunnableConfig | None = None,
) -> str:
    thread_id = state.get("thread_id")

    if isinstance(thread_id, str) and thread_id.strip():
        return thread_id

    configurable = config.get("configurable", {}) if config else {}
    configured_thread_id = configurable.get("thread_id")

    if isinstance(configured_thread_id, str) and configured_thread_id.strip():
        return configured_thread_id

    raise ValueError("Missing thread_id in workflow state/config.")


async def retrieval_memory(
    state: AgentState,
    config: RunnableConfig | None = None,
) -> dict[str, str]:
    """
    Return semantically similar memories for the current user message.

    The graph should continue even when long-term memory retrieval is unavailable.
    """

    user_message = _latest_user_message(state)
    thread_id = _resolve_thread_id(state, config)

    try:
        vector_store = await aget_vector_store()
        result = await vector_store.asimilarity_search(
            query=user_message,
            k=4,
            filter=Filter(
                must=[
                    FieldCondition(
                        key="metadata.user_id",
                        match=MatchValue(value=thread_id),
                    )
                ]
            ),
        )
    except Exception:
        logger.exception("Memory retrieval failed for thread_id=%s", thread_id)
        return {"retrieved_memories": NO_RELEVANT_MEMORIES}

    retrieved_memories = "\n".join(
        doc.page_content.strip()
        for doc in result
        if getattr(doc, "page_content", "").strip()
    )

    return {
        "retrieved_memories": retrieved_memories or NO_RELEVANT_MEMORIES,
    }
