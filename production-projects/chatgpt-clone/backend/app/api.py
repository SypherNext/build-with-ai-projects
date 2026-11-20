"""FastAPI app -- from the Build lesson's Step 2, plus:

- The CORS middleware the lesson's own "Common Errors" section (Error 1)
  tells you to add -- included here so the reference app actually runs
  against the Vite dev server without manual follow-up.
- A `POST /api/chat/stream` route. The lesson writes `stream_chat()` in
  Step 3 but never registers it as an endpoint, even though the Step 5
  frontend code calls `fetch('/api/chat/stream', ...)`. Wired up here so
  frontend and backend actually connect.
"""
import os
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.database import get_conn, init_db
from app.stream import stream_chat

app = FastAPI(title="ChatClone API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173")],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConversationCreate(BaseModel):
    title: str = "New Chat"
    model: str = "claude-haiku-5-5"
    system_prompt: str = "You are a helpful assistant."


class MessageCreate(BaseModel):
    role: str
    content: str
    tokens: int = 0


class ChatRequest(BaseModel):
    conversation_id: str
    message: str


@app.on_event("startup")
async def startup():
    init_db()


@app.get("/api/conversations")
def list_conversations():
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, title, model, created_at, updated_at FROM conversations ORDER BY updated_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/api/conversations")
def create_conversation(req: ConversationCreate):
    conn = get_conn()
    conv_id = uuid.uuid4().hex[:12]
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO conversations VALUES (?, ?, ?, ?, ?, ?)",
        (conv_id, req.title, req.model, req.system_prompt, now, now),
    )
    conn.commit()
    conn.close()
    return {"id": conv_id, "title": req.title}


@app.delete("/api/conversations/{conv_id}")
def delete_conversation(conv_id: str):
    conn = get_conn()
    conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
    conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
    conn.commit()
    conn.close()
    return {"deleted": True}


@app.get("/api/conversations/{conv_id}/messages")
def get_messages(conv_id: str):
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, role, content, tokens, created_at FROM messages WHERE conversation_id = ? ORDER BY created_at",
        (conv_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    try:
        return await stream_chat(req.conversation_id, req.message)
    except HTTPException:
        raise
