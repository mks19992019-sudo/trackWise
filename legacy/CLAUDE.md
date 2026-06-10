# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands
- Install dependencies: `uv sync`
- Run server: `uvicorn main:app --reload`
- Run tests: `pytest`
- Format code: `black .`
- Start dependencies: `docker compose up -d`

## Architecture
The project is a Finance AI System built with FastAPI and LangGraph.

### Core Components
- `main.py`: FastAPI application. Provides the `/chat` endpoint and manages short-term session TTL using Redis.
- `graph.py`: Defines the LangGraph state machine (`StateGraph`). It configures the `RedisSaver` for persistent agent check-pointing and connects the `ai_agent` node.
- `agent.py`: Implements the agent logic using `create_agent` from LangChain. This is where agent tools and system prompts (e.g., expense tracker expert) are defined.
- `llm.py`: Centralizes the LLM configuration (currently using `ChatGroq`).

### Data Flow
1. User sends a request to `/chat` with `message` and `thread_id`.
2. `main.py` updates a session key in Redis for TTL management.
3. `workflow.invoke` is called in `graph.py` using the `thread_id` for state recovery via `RedisSaver`.
4. The `ai_agent` node in `agent.py` processes the message and returns the response.

### Infrastructure
- **Redis**: Used for both LangGraph checkpointing and manual session tracking.
- **Postgres**: Configured in `docker-compose.yml` and `graph.py` (though currently commented out in favor of Redis).
