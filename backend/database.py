from psycopg import connect
from dotenv import load_dotenv
import os
load_dotenv()

def connect_db():
    conn = connect(os.getenv("DATABASE_URL"))
    if not conn:
        raise Exception("data base faild to connect")
    else:
    
        return conn


