# to store the vectore data base and easly convert it 
from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings

# to connect form docker cotiner 
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams,Distance





client = QdrantClient(
    host = 'localhost',
    port = 6333
)

# before embeding we need to crete memories in qdrant 
if not client.collection_exists("memories"):
    client.create_collection(
        collection_name="memories",
        vectors_config=VectorParams(
            size=768,
            distance=Distance.COSINE
        )
    )






embeding = HuggingFaceEmbeddings(
    model_name = "BAAI/bge-base-en-v1.5"
)



# this is the main .... with the help of that we easily save and sementic serch with that in our qdrant
vector_store = QdrantVectorStore.from_existing_collection(
    embedding=embeding,
    collection_name="memories",
    url ="http://localhost:6333"
)







