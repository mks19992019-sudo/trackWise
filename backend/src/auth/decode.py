import jwt
from src.config.settings import settings


def decode_token (token:str):
    result = jwt.decode(token,settings.JWT_SECRET_KEY,settings.JWT_ALGORITHM)

    return result