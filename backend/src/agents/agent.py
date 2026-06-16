from langchain.agents import create_agent
from .state import AgentState
from src.config.llm import model
from src.tools.tools import get_expenses , add_expenses , delete_expense , update_expense




async def agent(state:AgentState):

    msg=state['messages']
    AI_agent=create_agent(
    model = model,
    tools = [get_expenses,add_expenses,delete_expense,update_expense],
    system_prompt=f'''act like a expnace tracker here is the user_id{state["thread_id"]}You are TrackWise, an AI expense management assistant.

Rules:

1. Every expense operation must use the authenticated user's user_id.

2. Before updating or deleting an expense, if the expense_id is unknown,
   first call get_expenses(user_id) to identify the correct expense.

3. Never guess an expense_id.

4. If multiple expenses match the user's request, ask for clarification.

5. Always use tools to read or modify expense data.
   Never invent expense information.

6. When updating or deleting data, verify the target expense belongs
   to the current user.

7. Use budgets and expenses data from tools only.'''
)
    result =await AI_agent.ainvoke({'messages':msg})
    print(result)
   
    

    return {'messages':result["messages"]}








