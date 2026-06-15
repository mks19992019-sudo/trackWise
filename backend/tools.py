from database import connect_db
from langchain.tools import tool

@tool
async def get_expenses(user_id:int ):
    '''use this tools to get the expnce of user'''

    cnn = await connect_db()

    cur = cnn.cursor()
   
    await cur.execute(
        '''
        select * from expenses where user_id = %s''',(user_id,)
    )
    

    data = await cur.fetchall()

    await cur.close()

    await cnn.close()

    return data
    

@tool
async def add_expenses(
    user_id:int,
    amount:int,
    category:str,
    description:str
):
    '''Create a NEW expense.

Only use this when the user is recording a new purchase or spending.

Do NOT use this for deleting or modifying existing expenses.'''
    cnn = await connect_db()
    cur=cnn.cursor()

    await cur.execute(
        '''
    INSERT INTO expenses(user_id,amount,category,description)
    values (%s,%s,%s,%s)
''',(user_id,amount,category,description)
    )
    await cnn.commit()
    await cur.close()
    await cnn.close()

    return 'save the expence succesfully'



@tool
async def update_expense(
    user_id: int,
    expense_id: int,
    amount: int
):
    """Update expense amount
    If expense_id is unknown,

    first use get_expenses to locate

    the expense."""

    cnn = await connect_db()
    cur = cnn.cursor()

    await cur.execute(
        """
        UPDATE expenses
        SET amount = %s
        WHERE id = %s
        AND user_id = %s
        """,
        (amount, expense_id, user_id)
    )

    await cnn.commit()

    await cur.close()
    await cnn.close()

    return "Expense updated successfully"

@tool
async def delete_expense(
    user_id: int,
    expense_id: int
):
    """Delete an expense
    If expense_id is unknown,

    first use get_expenses to locate

    the expense."""

    cnn = await connect_db()
    cur = cnn.cursor()

    await cur.execute(
        """
        DELETE FROM expenses
        WHERE id = %s
        AND user_id = %s
        """,
        (expense_id, user_id)
    )

    await cnn.commit()

    await cur.close()
    await cnn.close()

    return "Expense deleted successfully"