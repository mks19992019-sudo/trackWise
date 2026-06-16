from __future__ import annotations
from contextlib import asynccontextmanager
from src.db.create_table import create_tb
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from src.routers.chat import chat_router
from dotenv import load_dotenv
from src.agents.graph import _initialize_resources , close_graph_resources



load_dotenv()


 
@asynccontextmanager
async def lifespan(_: FastAPI):
    await create_tb()
    await _initialize_resources()



    yield
    await close_graph_resources()
    print ("shuting down")



app = FastAPI(
    title="Finance AI System",
    description="AI-powered personal finance management",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def home():
    """Health check endpoint"""
    return {"message": "Finance AI System is running"}


app.include_router(chat_router)
