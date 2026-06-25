from fastapi import FastAPI
from .routers import chat

app = FastAPI(
    title= "agent learn",
    version="0.2.0"
)

app.include_router(chat.router)

@app.get("/")
async def root():
    return {"message":"HELLO WORLD"}