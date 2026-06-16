from jose import jwt
from src.config.settings import settings
from datetime import datetime , timedelta

def create_access_token(user_id: int):

    payload = {"user_id": user_id,
               "exp": datetime.now() + timedelta(minutes=5)}

    token = jwt.encode(payload,key=settings.JWT_SECRET_KEY,algorithm=settings.JWT_ALGORITHM)

    return token    