from langchain_core.tools import tool
from embeding import vector_store
from qdrant_client.models import   MatchValue , Filter , FieldCondition









# memory serch tool
@tool
def serch_memory(query:str,user_id:str):
    """
    Returns semantically similar memories.
    Some memories may be irrelevant.
    Use only memories relevant to the current question.

    """

    result = vector_store.similarity_search(query=query,k=4,filter=Filter(
        must=[FieldCondition(
            key="metadata.user_id",
            match=MatchValue(
                value=user_id
            )

        )]
    ))

    final_memory = ('/n'.join(docs.page_content for docs in result)
                    if result
                    else 'no memories found' )
    
    return final_memory


















