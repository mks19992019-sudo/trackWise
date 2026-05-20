from typing import TypedDict
from langgraph.graph  import MessagesState ,START , StateGraph
from agent import agent
from langchain_core.messages import HumanMessage


# building graph

grpah=StateGraph(MessagesState)



grpah.add_node('ai_agent',agent)

grpah.add_edge(START,'ai_agent')



workflow = grpah.compile()



result = workflow.invoke({'messages':[
    HumanMessage(content="kese ho")
]})


