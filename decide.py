
from embeding import vector_store
from llm import model
from pydantic import BaseModel 
from prompts import prompt1 , prompt2
from state import AgentState


class check(BaseModel):
    ans : bool


# first check the user query is genully need to add in 

struture_model = model.with_structured_output(check)

chain = prompt1 | struture_model

chain2 = prompt2 | struture_model



# to check the user query to store or not return true or fale
def check_store(query):
    
    result = chain.invoke({'query':query})
    print(result)
    return result.ans

# now we check this informetion is already present in vector data base or not 

def check_database(query,rerterival):

    return chain2.invoke({"query": query,"memories": rerterival}).ans

def decide_store_or_not(AgentState:AgentState):
    query = AgentState["messages"][-1].content
    Thread_id = AgentState["thread_id"]
    reterival = AgentState["retrieved_memories"]
    
    if check_store(query):
        if check_database(query,reterival):

            vector_store.add_texts(texts=[query],metadatas=[{
                "user_id" : Thread_id
            }])
        return {}
    return {}





    
    



