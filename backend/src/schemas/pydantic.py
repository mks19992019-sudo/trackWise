from typing import Annotated
from pydantic import BaseModel, ConfigDict, StringConstraints 


TrimmedText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

class ChatMessage(BaseModel):
    message: TrimmedText
    thread_id: TrimmedText


class GoogleLoginRequest(BaseModel):
    credential:str