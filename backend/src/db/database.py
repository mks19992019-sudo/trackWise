from psycopg import AsyncConnection 
from src.config.settings import settings


async def connect_db():
    conn = await AsyncConnection.connect(settings.DATABASE_URL)
    if not conn:
        raise Exception("data base faild to connect")
    else:
    
        return conn


