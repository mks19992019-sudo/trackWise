from typing import TypedDict
from langgraph.graph  import MessagesState ,START , StateGraph
from agent import agent
from langchain_core.messages import HumanMessage
#from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres import PostgresSaver



dataBase_url = 'postgresql://postgres:postgres@localhost:5442/postgres'


# building graph

grpah=StateGraph(MessagesState)



grpah.add_node('ai_agent',agent)

grpah.add_edge(START,'ai_agent')

checkpointer_cm = (PostgresSaver.from_conn_string(dataBase_url))

checkpointer = (checkpointer_cm.__enter__())

checkpointer.setup()



workflow = grpah.compile(checkpointer=checkpointer)






