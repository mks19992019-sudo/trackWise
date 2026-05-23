from fastapi import FastAPI
from pydantic import BaseModel
from graph import workflow
from langchain_core.messages import HumanMessage
from redis import Redis
from decide import process_memory


Redis_client = Redis(
    host='localhost',
    port=6379,
    decode_responses=True
)



class msg(BaseModel):
    message:str
    thread_id : str


app = FastAPI()


@app.get('/')
def Home():
    return {'message':"fast api is working"}

@app.post('/chat')
def chat(msg:msg):
    thread_id = msg.thread_id
    user_msg= msg.message

    session_key = f"session:{thread_id}"
    # redis ttl code
    # session create / update
    Redis_client.set(
        session_key ,'active' , ex=20
    )



    result = workflow.invoke({
        'messages':[HumanMessage(content=user_msg)],
        'thread_id':thread_id
    },{"configurable": {"thread_id": thread_id}})

    return result['messages'][-1].content


