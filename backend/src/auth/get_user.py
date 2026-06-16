from src.db.database import connect_db


async def get_user(google_id:str):
    conn = await connect_db()
    cur = conn.cursor()

    await cur.execute("""
    SELECT id FROM USERS 
    WHERE google_id = %s

""",(google_id,));
    
    data = await cur.fetchone()

    await cur.close()
    await conn.close()

    return {
        'id':data[0]
    }

    
    