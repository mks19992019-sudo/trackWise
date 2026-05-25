# TrackWise

An AI agent that manages your expenses through natural language. Just talk to it — it handles the rest.

---

## What it does

TrackWise lets you manage your finances by simply having a conversation.

- Add expenses in plain English
- Check your spending history
- Get summaries by category or date
- Set and track budgets
- Ask anything about your money

No forms. No spreadsheets. Just talk.



## Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent Framework | LangGraph + LangChain |
| Backend | FastAPI (async) |
| LLM | Groq (Llama) |
| Database | PostgreSQL |
| Vector Memory | Qdrant |
| Embeddings | HuggingFace BGE |
| Deployment | Docker |

---

## Architecture

```
User Message
     │
     ▼
FastAPI /chat
     │
     ▼
LangGraph Workflow
     │
     ├── Retrieval Node (long-term memory)
     ├── Memory Decision Node (what to store)
     └── AI Agent Node (tools + reasoning)
     │
     ▼
PostgreSQL + Qdrant
     │
     ▼
Response
```

---

## Memory System

**Short-term** — LangGraph checkpointer backed by PostgreSQL. Keeps conversation context across requests.

**Long-term** — Qdrant vector store. Remembers user preferences and patterns across sessions.

---

## Quick Start

**1. Clone**
```bash
git clone https://github.com/mks19992019-sudo/trackWise
cd trackWise
```

**2. Environment**
```bash
GROQ_API_KEY=your_key
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_key
```

**3. Start services**
```bash
docker compose up -d
```

**4. Run**
```bash
uv run uvicorn main:app --reload
```

API live at `http://localhost:8000`
Docs at `http://localhost:8000/docs`

---

## API

```
POST /chat

{
  "message": "I spent 500 rupees on groceries",
  "thread_id": "user-123"
}
```

---

## Example

```
User: I spent 1500 on groceries yesterday
AI:   Recorded ₹1,500 grocery expense for yesterday.

User: Show me my food expenses this month
AI:   You've spent ₹4,200 on food this month across 6 transactions.

User: Set a food budget of 5000 rupees
AI:   Monthly food budget of ₹5,000 created.
```

---

## Built by

**Mohit Kumar Suman**
[GitHub](https://github.com/mks19992019-sudo) · [LinkedIn](https://www.linkedin.com/in/mohit-kumar-suman-4ab261346/) · [Portfolio](https://protfoilo-ivory.vercel.app)