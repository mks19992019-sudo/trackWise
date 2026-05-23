
from langgraph.graph import  START, StateGraph
from agent import agent
from langgraph.checkpoint.redis import RedisSaver
from reterival import retrieval_memory
from decide import decide_store_or_not
from state import AgentState






# building graph
graph = StateGraph(AgentState)

# Add nodes
graph.add_node('retrieval_memory', retrieval_memory)
graph.add_node('decide_store_or_not', decide_store_or_not)
graph.add_node('ai_agent', agent)

# Add edges to create the flow: START -> retrieval_memory -> decide_store_or_not -> agent
graph.add_edge(START, 'retrieval_memory')
graph.add_edge('retrieval_memory', 'decide_store_or_not')
graph.add_edge('decide_store_or_not', 'ai_agent')

# Configure checkpointer
REDIS_URL = "redis://localhost:6379"
checkpointer_redis = RedisSaver.from_conn_string(REDIS_URL)
checkpointer = checkpointer_redis.__enter__()
checkpointer.setup()

# Compile the workflow
workflow = graph.compile(checkpointer=checkpointer)