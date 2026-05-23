from dotenv import load_dotenv
from langchain_groq import ChatGroq
import os

load_dotenv()



model = ChatGroq(model='llama-3.1-8b-instant')
