from llm import model
from langchain.agents import create_agent
from langgraph.graph  import MessagesState 



tools = []
agents = create_agent(
        model = model,
        tools=tools,
        system_prompt='you are a expnce tracker expert'
    )



def agent(state:MessagesState):

    return agents.invoke(state)
    
    






