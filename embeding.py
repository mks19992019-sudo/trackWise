import asyncio
import os
from functools import lru_cache
from typing import Any

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)
COLLECTION_NAME = "memories"
EMBEDDING_MODEL_NAME = "BAAI/bge-base-en-v1.5"

#1
@lru_cache
def get_qdrant_client() -> QdrantClient:
    return QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
    )


#2
def ensure_collection_exists(client: QdrantClient) -> None:
    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=768,
                distance=Distance.COSINE,
            ),
    )

    # Create keyword index for user_id filtering (safe to call multiple times)
    try:
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="metadata.user_id",
            field_schema="keyword",
        )
    except Exception:
        # Index might already exist, that's ok
        pass

#3
@lru_cache
def get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

#4
@lru_cache
def get_vector_store() -> QdrantVectorStore:
    client = get_qdrant_client()
    ensure_collection_exists(client)

    return QdrantVectorStore.from_existing_collection(
        embedding=get_embeddings(),
        collection_name=COLLECTION_NAME,
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
    )


class LazyVectorStoreProxy:
    def __getattr__(self, name: str) -> Any:
        return getattr(get_vector_store(), name)


vector_store = LazyVectorStoreProxy()


#5
async def aget_vector_store() -> QdrantVectorStore:
    return await asyncio.to_thread(get_vector_store)