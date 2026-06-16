from src.db.database import connect_db


async def create_user(email:str,google_id:str):
    conn = await connect_db()
    cur = conn.cursor()

    await cur.execute("""
    INSERT INTO users(email,google_id)
    VALUES (%s,%s)

""")(email,google_id)
    
    await conn.commit()

    await cur.close()
    await conn.close()

