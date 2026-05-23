from decide import chain

#print(chain.invoke({'query':'hi i am mohit'}))

from pydantic import BaseModel

from llm import model

class Check(BaseModel):

    ans: bool

structured = model.with_structured_output(Check)

print(

    structured.invoke("Return false")

)
