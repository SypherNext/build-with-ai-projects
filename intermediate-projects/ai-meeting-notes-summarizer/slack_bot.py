"""AI Meeting Notes Summarizer -- FastAPI/Slack web deployment of the
summarizer.py CLI tool, from the Improve-and-Deploy lesson's Deploy It section."""

import os
import sys

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")
if not ANTHROPIC_API_KEY:
    print("Error: ANTHROPIC_API_KEY not set")
    sys.exit(1)

import anthropic

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Import your summarizer functions
from summarizer import detect_meeting_type, summarize_transcript

app = FastAPI(title="Meeting Notes Slack Bot")


@app.post("/slack/events")
async def slack_events(request: Request):
    body = await request.json()
    # URL verification
    if body.get("type") == "url_verification":
        return JSONResponse(content={"challenge": body["challenge"]})
    # Handle message with transcript
    if "event" in body:
        event = body["event"]
        if event.get("type") == "message" and "text" in event:
            transcript = event["text"]
            meeting_type = detect_meeting_type(transcript)
            summary = summarize_transcript(transcript, meeting_type)
            return JSONResponse(content={"summary": summary})
    return JSONResponse(content={"ok": True})


@app.get("/")
async def index():
    return {"status": "Meeting Notes Bot is running"}
