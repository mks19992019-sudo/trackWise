from google.oauth2 import id_token

from google.auth.transport import requests
from src.config.settings import settings



async def verify_google_token(token: str):

    data = id_token.verify_oauth2_token(token,requests.Request(),settings.GOOGLE_CLIENT_ID)

    return  data