"""FastAPI entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import admin, chat, faq

app = FastAPI(
    title="Medical FAQ API",
    description="Retrieval-based chatbot + auto-FAQ pipeline. No LLM.",
    version="0.1.0",
)

# CORS for the Next.js dev server. Tighten for production deployments.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(faq.router, prefix="/faq", tags=["faq"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])


@app.get("/health")
async def health():
    return {"status": "ok"}
