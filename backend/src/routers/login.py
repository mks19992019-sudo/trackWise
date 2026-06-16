from fastapi import APIRouter
from src.schemas.pydantic import GoogleLoginRequest
from src.auth.google import verify_google_token
from src.auth.get_user import get_user
from src.auth.create_user import create_user
from src.auth.jwt import create_access_token


login_route = APIRouter()



@login_route.post("/login")
async def check_user(data:GoogleLoginRequest):

    google_data = verify_google_token(data.credential)
    google_id = google_data['sub']
    email = google_data['email']

    user = await get_user(google_id)
    if not user:
        user = await create_user(email=email,google_id=google_id)

    token = await create_access_token(user[user_id])
    








    


    

