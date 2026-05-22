from langchain_core.prompts import ChatPromptTemplate






check_query_is_imp = ChatPromptTemplate.from_template(
    """

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





"""

)



check_to_store= ChatPromptTemplate.from_template("""
You are a memory deduplication system.

Your task is to determine whether the user's new message contains information that should be added to long-term memory.

You will receive:

1. The current user message.
2. Existing memories retrieved from the vector database.

Rules:

- Return true if the user message contains new information that is not already present in the existing memories.
- Return true if the message significantly updates or changes an existing memory.
- Return false if the information is already known.
- Return false if the message is semantically equivalent to an existing memory.
- Return false if the message only rephrases information that already exists.
- Compare meaning, not exact wording.
- Be conservative and avoid storing duplicate memories.

Examples:

User Message:
"My favorite programming language is Python"

Existing Memories:
- "User prefers Python for development"

Output:
False

---

User Message:
"I am building a finance AI system"

Existing Memories:
- "User likes Python"

Output:
True

---

User Message:
"I now prefer Go instead of Python"

Existing Memories:
- "User prefers Python for development"

Output:
True

---

User Message:
"I use Redis for short term memory"

Existing Memories:
- "User uses Redis in AI projects"

Output:
False

Return ONLY a boolean:

True
or
False

Current User Message:
{query}

Existing Memories:
{memories}"""
)

prompt1= check_query_is_imp
prompt2 = check_to_store