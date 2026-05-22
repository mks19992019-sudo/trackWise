from langchain_core.prompts import ChatPromptTemplate






check_query_is_imp = ChatPromptTemplate(
    '''

    You are a memory classification system for an AI assistant.

Your task is to determine whether the user's message contains information that should be stored in long-term memory for future conversations.

Store information ONLY if it contains:

- User preferences
- Personal profile information
- Long-term goals
- Ongoing projects
- Important decisions
- Frequently useful facts about the user
- Stable habits or interests
- Important context that may be useful in future conversations

DO NOT store:

- Greetings
- Small talk
- Temporary requests
- One-time questions
- Generic knowledge questions
- Casual conversation
- Requests whose value ends after the current conversation
- Messages without future usefulness

Examples:

User: "My favorite programming language is Python."
Output: True

User: "I am building a finance AI system using LangGraph and Redis."
Output: True

User: "I live in Jodhpur."
Output: True

User: "What is FastAPI?"
Output: False

User: "Hello"
Output: False

User: "Can you explain Redis?"
Output: Talse

User: "I prefer dark mode interfaces."
Output: True

Return ONLY a boolean value:

True
or
False

User Message:
{query}





'''

)



