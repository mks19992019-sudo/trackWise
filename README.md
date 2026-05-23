# AI Expense Tracker Agent

A production-oriented AI-powered expense tracking assistant built with FastAPI, LangGraph, PostgreSQL, Redis, Qdrant, and modern LLM tooling.

The system combines conversational AI, persistent memory, tool calling, and structured financial data management to help users track expenses, manage budgets, and gain insights through natural language interactions.

---

## Features

### Expense Management

- Add expenses using natural language
- Update existing expenses
- Delete expenses
- Search expenses
- Categorize spending
- Monthly spending summaries
- Budget creation and tracking
- Financial insights and analytics

### AI Agent Capabilities

- Conversational expense management
- Tool calling architecture
- Multi-step reasoning workflow
- Structured outputs
- Context-aware responses

### Memory System

#### Short-Term Memory

- LangGraph checkpointing
- Redis-backed conversation persistence
- Session continuity

#### Long-Term Memory

- Qdrant vector database
- Semantic memory retrieval
- User preference storage
- Personalized interactions

### Backend Architecture

- FastAPI REST API
- Async-first architecture
- PostgreSQL persistence layer
- Redis caching and checkpoints
- Vector memory retrieval
- Modular service design

---

## System Architecture

```text
User
 │
 ▼
FastAPI API Layer
 │
 ▼
LangGraph Workflow
 │
 ├── Retrieval Memory Node
 │
 ├── AI Agent Node
 │
 └── Tool Execution Layer
 │
 ▼
Business Services
 │
 ├── PostgreSQL
 │
 ├── Redis
 │
 └── Qdrant
 │
 ▼
Response Generation
 │
 ▼
User
```

---

## Tech Stack

### Backend

- FastAPI
- Python 3.14
- Pydantic

### Agent Framework

- LangGraph
- LangChain
- Create React Agent

### Databases

- PostgreSQL
- Redis
- Qdrant

### AI Models

- Groq
- Llama Models
- Compatible with OpenAI
- Compatible with Anthropic

### Infrastructure

- Docker
- Docker Compose
- Async Architecture

---

## Project Structure

```text
app/
│
├── api/
├── graph/
├── agent/
├── memory/
├── tools/
├── database/
├── services/
├── models/
├── schemas/
├── config/
│
├── main.py
│
tests/
│
docker/
│
README.md
```

---

## Agent Workflow

Current workflow:

```text
START
 │
 ▼
retrieval_memory
 │
 ▼
ai_agent
 │
 ▼
END
```

Future workflow:

```text
START
 │
 ▼
retrieval_memory
 │
 ▼
decide_store_or_not
 │
 ▼
ai_agent
 │
 ▼
END
```

---

## Memory Architecture

### Short-Term Memory

Purpose:

- Preserve conversation state
- Session continuity
- Multi-turn reasoning

Technology:

- LangGraph Checkpointer
- Redis

### Long-Term Memory

Purpose:

- Store user preferences
- Budget preferences
- Financial goals
- Important personal context

Technology:

- Qdrant Vector Database
- Semantic Retrieval

---

## Getting Started

### Clone Repository

```bash
git clone https://github.com/your-username/expense-tracker-agent.git

cd expense-tracker-agent
```

### Create Virtual Environment

```bash
python -m venv .venv

source .venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file:

```env
POSTGRES_URL=
REDIS_URL=
QDRANT_URL=
QDRANT_API_KEY=

GROQ_API_KEY=

LANGCHAIN_API_KEY=
LANGCHAIN_TRACING_V2=true
```

---

## Run PostgreSQL

```bash
docker compose up -d postgres
```

---

## Run Redis

```bash
docker compose up -d redis
```

---

## Run Qdrant

```bash
docker compose up -d qdrant
```

---

## Run Application

```bash
uvicorn app.main:app --reload
```

Server:

```text
http://localhost:8000
```

Swagger:

```text
http://localhost:8000/docs
```

---

## Example Request

```json
{
  "thread_id": "user-123",
  "message": "I spent 500 rupees on groceries today"
}
```

Example Response:

```json
{
  "response": "I've recorded a grocery expense of ₹500."
}
```

---

## Testing

Run tests:

```bash
pytest
```

Run coverage:

```bash
pytest --cov
```

---

## Deployment

Recommended:

- Docker
- Railway
- Render
- Fly.io
- DigitalOcean
- AWS ECS
- Kubernetes

---

## Roadmap

- [x] FastAPI backend
- [x] LangGraph workflow
- [x] Redis checkpointing
- [x] Qdrant memory retrieval
- [x] Async architecture
- [ ] Budget analytics
- [ ] Long-term memory classification
- [ ] Financial recommendations
- [ ] Multi-user dashboard
- [ ] Notification system
- [ ] Mobile integration

---

## License

MIT License

---

## Author

Mohit Kumar

Building practical AI agents, memory systems, and intelligent automation workflows.