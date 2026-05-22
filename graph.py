from typing import TypedDict
from langgraph.graph  import MessagesState ,START , StateGraph
from agent import agent
from langchain_core.messages import HumanMessage
#from langgraph.checkpoint.memory import InMemorySaver
#from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.redis import RedisSaver
from qdrant_client.models import Filter, FieldCondition, MatchValue


#dataBase_url = 'postgresql://postgres:postgres@localhost:5442/postgres'

REDIS_URL = "redis://localhost:6379"


# building graph

grpah=StateGraph(MessagesState)



grpah.add_node('ai_agent',agent)

grpah.add_edge(START,'ai_agent')

#checkpointer_postgres = (PostgresSaver.from_conn_string(dataBase_url))


checkpointer_redis = RedisSaver.from_conn_string(REDIS_URL)

# first we open that the pakage using the enter 
# like we open file with 'with f as f'
checkpointer = checkpointer_redis.__enter__()

#checkpointer = (checkpointer_postgres.__enter__())

checkpointer.setup()




workflow = grpah.compile(checkpointer=checkpointer)







