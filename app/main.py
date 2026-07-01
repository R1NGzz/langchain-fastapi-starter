from fastapi import FastAPI
from .routers import chat, rag

app = FastAPI(title="agent learn", version="0.3.0")

app.include_router(chat.router)
app.include_router(rag.router)


@app.get("/")
async def root():
    return {"message": "HELLO WORLD"}
