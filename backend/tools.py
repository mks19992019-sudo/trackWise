from database import connect_db
from langchain.tools import tool




#data = cur.fetchall()



#cur.close()

#cnn.close()


@tool
def get_expenses(user_id:int ):
    '''use this tools to get the expnce of user'''

    cnn = connect_db()

    cur = cnn.cursor()
   
    cur.execute(
        '''
        select * from expenses where user_id = %s''',(user_id,)
    )
    

    data = cur.fetchall()

    cur.close()

    cnn.close()

    return data
    

@tool
def add_expenses(
    user_id:int,
    amount:int,
    category:str,
    description:str
):
    '''use this tool to add the expence '''
    cnn = connect_db()
    cur=cnn.cursor()

    cur.execute(
        '''
    INSERT INTO expenses(user_id,amount,category,description)
    values (%s,%s,%s,%s)
''',(user_id,amount,category,description)
    )
    cnn.commit()
    cur.close()
    cnn.close()

    return 'save the expence succesfully'



