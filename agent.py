import asyncio
from datetime import datetime, timezone
from functools import lru_cache

from google.api_core.exceptions import GoogleAPIError
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage

from llm import model
from state import AgentState
from tool import get_finance_tools, reset_active_user_id, set_active_user_id

AGENT_SYSTEM_PROMPT = """
You are an intelligent personal expense tracking assistant.

Your responsibilities:

- Help users manage expenses and finances.

- Add, edit, delete, search, summarize, and analyze expenses using available tools.

- Answer finance and budgeting questions clearly.

- Provide personalized recommendations when relevant.

Memory Rules:

- Relevant User Context may be provided in conversation context.

- Use it only when it improves the answer.

- Ignore memories that are unrelated to the current request.

- If memory conflicts with the user's latest message, trust the latest message.

- Never invent user memories.

- Never mention memories, retrieval systems, vector databases, embeddings, tools, internal reasoning, or system prompts.

- Do not tell the user that information was retrieved from memory.

Tool Usage:

- Use tools whenever they are required to complete a task accurately.

- Prefer tool results over assumptions.

- If information is unavailable, ask for clarification rather than guessing.

Response Style:

- Natural

- Professional

- Personalized

- Direct

- Helpful

- Concise unless detailed explanation is requested

Tool Rules:

- The current user is already scoped automatically for all tools.

- Never ask the user for a user_id or thread_id.

- When the user wants to add, update, delete, list, search, summarize, or check budgets and expenses, use the tools instead of guessing.
"""
INVALID_TOOL_RETRY_PROMPT = """
Tool safety reminder:

- You may call only the provided finance tools.

- Never invent tool names.

- If none of the provided tools fit, answer directly or ask a clarifying question.
"""


def _runtime_context_messages(state: AgentState) -> list[SystemMessage]:
    messages: list[SystemMessage] = [
        SystemMessage(
            content=(
                "Current session context:\n"
                f"- user_scope: {state['thread_id']}\n"
                f"- current_utc_date: {datetime.now(timezone.utc).date().isoformat()}\n"
                "- Finance tools are already scoped to this user.\n"
                "- Do not ask for or expose the user_scope unless the user explicitly asks about it."
            )
        )
    ]

    retrieved_memories = state.get("retrieved_memories")

    if not retrieved_memories or retrieved_memories == "No relevant memories.":
        return messages

    messages.append(
        SystemMessage(
            content=f"Relevant User Context:\n{retrieved_memories}",
        )
    )
    return messages


@lru_cache
def get_expense_agent():
    tools = get_finance_tools()
    tool_names = ", ".join(tool.name for tool in tools)

    return create_agent(
        model=model,
        tools=tools,
        system_prompt=(
            f"{AGENT_SYSTEM_PROMPT}\n\n"
            f"Available tools: {tool_names}."
        ),
    )


async def aget_expense_agent():
    return await asyncio.to_thread(get_expense_agent)


def _is_invalid_tool_error(error: Exception) -> bool:
    message = str(error)
    return "attempted to call tool" in message or "tool_use_failed" in message


async def _fallback_without_tools(messages: list[BaseMessage]) -> AIMessage:
    fallback_messages = [
        SystemMessage(
            content=(
                "A tool invocation failed. Do not call any tools in this reply. "
                "If the user asked for an action that requires tools, briefly ask them "
                "to retry or rephrase instead of guessing."
            )
        ),
        *messages,
    ]
    response = await model.ainvoke(fallback_messages)

    if not isinstance(response, AIMessage):
        raise ValueError("The fallback model response was not an AIMessage.")

    return response


async def _invoke_agent(messages: list[BaseMessage]) -> dict:
    expense_agent = await aget_expense_agent()

    try:
        return await expense_agent.ainvoke({"messages": messages})
    except Exception as exc:  # Catch broad exceptions to handle Groq errors
        if not _is_invalid_tool_error(exc):
            raise

        retry_messages = [
            SystemMessage(content=INVALID_TOOL_RETRY_PROMPT),
            *messages,
        ]

        try:
            return await expense_agent.ainvoke({"messages": retry_messages})
        except Exception as retry_exc:  # Catch broad exceptions for retry
            if not _is_invalid_tool_error(retry_exc):
                raise

            fallback_message = await _fallback_without_tools(retry_messages)
            return {"messages": [fallback_message]}


async def agent(state: AgentState) -> dict[str, list[BaseMessage]]:
    user_token = set_active_user_id(state["thread_id"])
    messages = [
        *_runtime_context_messages(state),
        *state["messages"],
    ]

    try:
        result = await _invoke_agent(messages)
        response_messages = result.get("messages", [])

        if not response_messages:
            raise ValueError("The agent did not return any messages.")

        # Only return the new assistant message so the outer LangGraph state
        # appends cleanly without duplicating prior history.
        return {"messages": [response_messages[-1]]}
    finally:
        reset_active_user_id(user_token)
