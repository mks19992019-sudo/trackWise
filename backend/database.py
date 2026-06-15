from psycopg import AsyncConnection
from dotenv import load_dotenv
import os
load_dotenv()

async def connect_db():
    conn = await AsyncConnection.connect(os.getenv("DATABASE_URL"))
    if not conn:
        raise Exception("data base faild to connect")
    else:
    
        return conn


