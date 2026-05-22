'''
    Here we decide whether the user's query is stored in the long term memory or not. 

'''

from embeding import vector_store
from llm import model

from pydantic import BaseModel 
from typing import Literal
from prompts import check_query_is_imp ,check_to_store
from qdrant_client.models import Filter, FieldCondition, MatchValue



class check(BaseModel):
    ans : bool


    




# first check the user query is genully need to add in 

struture_model = model.with_structured_output(check)

chain = check_query_is_imp | struture_model

chain2 = check_to_store | struture_model



# to check the user query to store or not return true or fale
def check_store(query):
    return chain.invoke({'query':query}).ans

# now we check this informetion is already present in vector data base or not 

def check_database(id,query):
    

    # sementic serch 
    search = vector_store.similarity_search(query=query,k=5,filter=Filter(
        must=[FieldCondition(
            key="metadata.user_id",
            match=MatchValue(
                value=id
            )

        )]
    ))

    memories = ('\n'.join(doc.page_content for doc in search)
                if search
                else 'no memories found')

    return chain2.invoke({"query": query,"memories": memories}).ans

    


def process_memory(id,query):


    if check_store(query):
        if check_database(id,query):
            vector_store.add_texts(texts=[query],metadatas=[{
                "user_id" : id
            }])
        return 
    return 





    
    



