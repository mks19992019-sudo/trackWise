from .database import connect_db

import asyncio

async def create_tb():
    conn = await connect_db()
    cur = conn.cursor()

    await cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
               id SERIAL PRIMARY KEY,
               email VARCHAR(200),
               google_id VARCHAR(200),
               creted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
            """)
    await cur.execute("""

    CREATE TABLE IF NOT EXISTS profiles(
        id SERIAL PRIMARY KEY,
        user_id INT REFERENCES users(id),
        monthly_income NUMERIC(10,2),
        currency VARCHAR(10),
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
    
    """)
    await cur.execute("""

    CREATE TABLE IF NOT EXISTS expenses(
        id SERIAL PRIMARY KEY,
        user_id INT REFERENCES users(id),
        amount NUMERIC(10,2),
        category VARCHAR(50),
        description TEXT
    );
    """)

    await cur.execute("""
    CREATE TABLE IF NOT EXISTS budgets(
        id SERIAL PRIMARY KEY,
        user_id INT REFERENCES users(id),
        category VARCHAR(50),
        monthly_limit NUMERIC(10,2)

    );

    """)
    await conn.commit()
    await cur.close()
    await conn.close()
    

    

    
