"""Streaming chat endpoint logic -- from the Build lesson's Step 3.

Fix applied: the lesson's snippet raised `HTTPException` without importing
it. Also wires in `count_tokens` (app/tokens.py) when saving the assistant
message, so the "token usage tracking" feature described in the
Architecture lesson actually records a token count (the lesson defined
`count_tokens` in the Deploy stage but never called it).
"""
import json
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sse_starlette.sse import EventSourceResponse

from app.database import get_conn
from app.providers import get_provider
from app.tokens import count_tokens


async def stream_chat(conversation_id: str, message: str):
    conn = get_conn()
    conv = conn.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,)).fetchone()
    if not conv:
        conn.close()
        raise HTTPException(404, "Conversation not found")

    # Save user message
    msg_id = uuid.uuid4().hex[:12]
    conn.execute(
        "INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?)",
        (msg_id, conversation_id, "user", message, count_tokens(message), datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()

    # Get conversation history
    messages = conn.execute(
        "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY created_at",
        (conversation_id,),
    ).fetchall()
    conn.close()

    # Get provider
    provider = get_provider(conv["model"])

    async def event_generator():
        full_response = ""
        async for chunk in provider.stream(conv["system_prompt"], [dict(m) for m in messages]):
            full_response += chunk
            yield {"event": "token", "data": json.dumps({"token": chunk})}

        # Save assistant message
        conn = get_conn()
        conn.execute(
            "INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?)",
            (
                uuid.uuid4().hex[:12],
                conversation_id,
                "assistant",
                full_response,
                count_tokens(full_response),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), conversation_id),
        )
        conn.commit()
        conn.close()

        yield {"event": "done", "data": json.dumps({"full": full_response})}

    return EventSourceResponse(event_generator())
