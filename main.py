from fastapi import FastAPI
from pydantic import BaseModel
from graph import workflow
from langchain_core.messages import HumanMessage


class msg(BaseModel):
    message:str



app = FastAPI()



@app.get('/')
def Home():
    return {'message':"fast api is working"}

@app.post('/chat')
def chat(msg:msg):
    user_msg= msg.message

    result = workflow.invoke({
        'messages':[HumanMessage(content=user_msg)]
    })

    return result['messages'][-1].content


