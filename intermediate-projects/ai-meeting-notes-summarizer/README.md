# AI Meeting Notes Summarizer

Reference implementation for the "AI Meeting Notes Summarizer" Intermediate
Project in Sypher's `build-with-ai` course. A CLI tool that takes a raw
meeting transcript, detects the meeting type (standup, retro, planning,
one-on-one, brainstorming, or general), and uses Claude Haiku to extract a
structured Markdown summary -- decisions, action items, blockers, and open
questions -- tailored to that meeting type.

This is the finished, verified version -- type the lesson's own steps
yourself first; come back here to compare your output or see it run.

- `summarizer.py` -- the CLI tool from the Build lesson (paste a transcript or load one from a file, get a structured summary back)
- `slack_bot.py` -- the FastAPI/Slack web deployment from the Deploy stage (forward a meeting transcript in Slack, get a summary back)
- `Dockerfile` -- builds `slack_bot.py` into a container image (verified locally only; no cloud deployment was provisioned for this reference)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env        # then add your ANTHROPIC_API_KEY
```

## Run the CLI

```bash
python summarizer.py
```

## Run the web app locally

```bash
uvicorn slack_bot:app --reload
# then open http://localhost:8000
```

## Build the Docker image locally

```bash
docker build -t ai-meeting-notes-summarizer .
docker run -p 8000:8000 --env-file .env ai-meeting-notes-summarizer
```
