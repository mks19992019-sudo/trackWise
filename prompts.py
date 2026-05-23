from langchain_core.prompts import ChatPromptTemplate

check_query_is_imp = ChatPromptTemplate.from_template("""
Decide if this user message should be stored in long-term memory.

Store:
- preferences
- personal information
- goals
- projects
- important user facts

Do not store:
- greetings
- small talk
- temporary requests
- generic questions

Message:
{query}

Return True or False.
""")


check_to_store = ChatPromptTemplate.from_template("""
Decide if this message contains new information compared to existing memories.

Return False if the information already exists or has the same meaning.

Message:
{query}

Memories:
{memories}

Return True or False.
""")

prompt1 = check_query_is_imp
prompt2 = check_to_store