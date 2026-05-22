# to store the vectore data base and easly convert it 
from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings

# to connect form docker cotiner 
from qdrant_client import QdrantClient


client = QdrantClient(
    host = 'localhost',
    port = 6333
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






