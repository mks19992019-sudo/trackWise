# Finance AI System v2

A sophisticated AI assistant specialized in expense tracking and financial management, featuring a dual-memory architecture (Short-term and Long-term) for personalized user experiences.

## 🚀 Overview

This system leverages a state-of-the-art agentic workflow to manage financial data. It doesn't just answer questions; it remembers user preferences, goals, and habits across different sessions using a combination of Redis and Qdrant.

### Key Features
- **Agentic Workflow**: Powered by LangGraph for complex state management.
- **Short-Term Memory**: Implemented via Redis for fast session recovery and thread-based state persistence.
- **Long-Term Memory**: Powered by Qdrant vector database to store and retrieve persistent user profile information.
- **Intelligent Memory Filtering**: A dedicated decision layer (`decide.py`) that analyzes whether information is worth storing for the long term, preventing database clutter with trivial conversation.
- **High-Performance LLM**: Integration with Groq for low-latency responses.

## 🛠️ Architecture

### Memory System
- **L1 (Short-Term)**: `RedisSaver` in LangGraph manages the current conversation state. Session TTL is handled in `main.py` to manage active users.
- **L2 (Long-Term)**: `QdrantVectorStore` stores embeddings of critical user information. The system uses a classification prompt (`prompts.py`) to decide if a message should be archived.

### Component Breakdown
- `main.py`: The entry point. A FastAPI server providing the `/chat` endpoint.
- `graph.py`: The brain of the operation. Orchestrates the LangGraph state machine.
- `agent.py`: Defines the agent's behavior, tools, and system persona ("Expense Tracker Expert").
- `decide.py`: The logic for memory classification (True/False) to determine L2 storage.
- `embeding.py`: Handles vectorization and connection to the Qdrant database.
- `llm.py`: Central configuration for the underlying Large Language Model.

## 📦 Installation & Setup

### Prerequisites
- Python 3.13+
- Docker and Docker Compose

### Quick Start
1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd v2
   ```

2. **Start Infrastructure**
   Launch Redis and Postgres containers:
   ```bash
   docker compose up -d
   ```
   *Note: Ensure Qdrant is also running on port 6333.*

3. **Install Dependencies**
   ```bash
   uv sync
   ```

4. **Environment Configuration**
   Create a `.env` file with your required API keys:
   ```env
   GROQ_API_KEY=your_key_here
   ```

5. **Run the Application**
   ```bash
   uvicorn main:app --reload
   ```

## 📡 API Reference

### Chat Endpoint
`POST /chat`

**Request Body:**
```json
{
  "message": "I prefer tracking my expenses in USD",
  "thread_id": "user_1234"
}
```

**Response:**
`"The agent's response string"`

## 🛠️ Tech Stack
- **Framework**: FastAPI
- **Orchestration**: LangGraph / LangChain
- **LLM**: Groq (GPT-OSS-120B)
- **Vector DB**: Qdrant
- **State Store**: Redis
- **Embeddings**: HuggingFace (`BGE-base-en-v1.5`)