import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import chat, conversations, data
from .services.store import store

app = FastAPI(title="Game Trend AI Chat API", version="1.0.0", description="Firestore data CRUD, summary context injection, and conversation storage.")
origins = [x.strip() for x in os.getenv("ALLOWED_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500").split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(data.router)
app.include_router(conversations.router)
app.include_router(chat.router)

@app.get("/", tags=["health"])
def health():
    return {"status": "ok", "storage": store.mode, "docs": "/docs"}
