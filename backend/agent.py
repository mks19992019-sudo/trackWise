from langchain.agents import create_agent
from state import AgentState
from llm import model
from tools import get_expenses , add_expenses




async def agent(state:AgentState):

    msg=state['messages']
    AI_agent=create_agent(
    model = model,
    tools = [get_expenses,add_expenses],
    system_prompt=f'act like a expnace tracker here is the user_id{state["thread_id"]}'
)
    result =await AI_agent.ainvoke({'messages':msg})

    return {'messages':result["messages"]}








