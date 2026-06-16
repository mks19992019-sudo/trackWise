from src.db.database import connect_db


async def create_user(email:str,google_id:str):
    conn = await connect_db()
    cur = conn.cursor()

    await cur.execute("""
    INSERT INTO users(email,google_id)
    VALUES (%s,%s)
                      
    RETURNING id
""",(email,google_id));

    # when we add a new user with that we also reterive the id that time so we get [(3,)]
    user_id = await cur.fetchone()

    
    await conn.commit()

    await cur.close()
    await conn.close()


    return {
        'id':user_id[0]
    }


