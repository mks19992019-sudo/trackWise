from fastapi import APIRouter , HTTPException
from src.schemas.pydantic import ChatMessage
from langchain_core.messages import HumanMessage
from src.agents.graph import get_workflow


chat_router  = APIRouter()


@chat_router.post("/chat")
async def chat(payload: ChatMessage):
    """Main chat endpoint - AI agent processes user messages"""
    thread_id = payload.thread_id
    user_message = payload.message
    

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