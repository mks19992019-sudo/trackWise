from langchain.agents import create_agent
from state import AgentState
from llm import model


AI_agent=create_agent(
    model = model,
    tools = [],
    system_prompt='act like a expnace tracker'
)

def agent(state:AgentState):

    msg=state['messages']
    result = AI_agent.invoke({'messages':msg})

    return {'messages':result["messages"]}







