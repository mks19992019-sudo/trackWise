import asyncio
from functools import lru_cache
from typing import Any

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "memories"
EMBEDDING_MODEL_NAME = "BAAI/bge-base-en-v1.5"


@lru_cache
def get_qdrant_client() -> QdrantClient:
    return QdrantClient(
        host=QDRANT_HOST,
        port=QDRANT_PORT,
    )


def ensure_collection_exists(client: QdrantClient) -> None:
    if client.collection_exists(COLLECTION_NAME):
        return

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=768,
            distance=Distance.COSINE,
        ),
    )


@lru_cache
def get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)


@lru_cache
def get_vector_store() -> QdrantVectorStore:
    client = get_qdrant_client()
    ensure_collection_exists(client)

    return QdrantVectorStore.from_existing_collection(
        embedding=get_embeddings(),
        collection_name=COLLECTION_NAME,
        url=f"http://{QDRANT_HOST}:{QDRANT_PORT}",
    )


class LazyVectorStoreProxy:
    def __getattr__(self, name: str) -> Any:
        return getattr(get_vector_store(), name)


vector_store = LazyVectorStoreProxy()


async def aget_vector_store() -> QdrantVectorStore:
    return await asyncio.to_thread(get_vector_store)
