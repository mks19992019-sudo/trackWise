
from langchain_core.tools import tool
from embeding import vector_store
from qdrant_client.models import   MatchValue , Filter , FieldCondition
from state import AgentState




def retrieval_memory(state:AgentState):
    """
    Returns semantically similar memories.
    Some memories may be irrelevant.
    Use only memories relevant to the current question.

    """
    user_msg = state['messages'][-1].content
    thread_id = state['thread_id']

    result = vector_store.similarity_search(query=user_msg,k=4,filter=Filter(
        must=[FieldCondition(
            key="metadata.user_id",
            match=MatchValue(
                value=thread_id
            )

        )]
    ))

    final_memory = ('\n'.join(docs.page_content for docs in result)
                    if result
                    else 'No relevant memories.' )
    
    return {
        'retrieved_memories':final_memory
        
    }