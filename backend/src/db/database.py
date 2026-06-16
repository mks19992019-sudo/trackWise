from psycopg import AsyncConnection
from dotenv import load_dotenv
import os
from src.config.settings import settings
load_dotenv()

async def connect_db():
    conn = await AsyncConnection.connect(settings.DATABASE_URL)
    if not conn:
        raise Exception("data base faild to connect")
    else:
    
        return conn


