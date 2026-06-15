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
    '''Create a NEW expense.

Only use this when the user is recording a new purchase or spending.

Do NOT use this for deleting or modifying existing expenses.'''
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



@tool
def update_expense(
    user_id: int,
    expense_id: int,
    amount: int
):
    """Update expense amount
    If expense_id is unknown,

    first use get_expenses to locate

    the expense."""

    cnn = connect_db()
    cur = cnn.cursor()

    cur.execute(
        """
        UPDATE expenses
        SET amount = %s
        WHERE id = %s
        AND user_id = %s
        """,
        (amount, expense_id, user_id)
    )

    cnn.commit()

    cur.close()
    cnn.close()

    return "Expense updated successfully"

@tool
def delete_expense(
    user_id: int,
    expense_id: int
):
    """Delete an expense
    If expense_id is unknown,

    first use get_expenses to locate

    the expense."""

    cnn = connect_db()
    cur = cnn.cursor()

    cur.execute(
        """
        DELETE FROM expenses
        WHERE id = %s
        AND user_id = %s
        """,
        (expense_id, user_id)
    )

    cnn.commit()

    cur.close()
    cnn.close()

    return "Expense deleted successfully"