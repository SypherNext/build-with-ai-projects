# ChatGPT Clone

Reference implementation for the "ChatGPT Clone" Production Project in
Sypher's `build-with-ai` course. A full-stack ChatGPT alternative: a
FastAPI backend that streams responses over Server-Sent Events from
Claude, GPT-4o-mini, or a local Ollama model, backed by SQLite, and a
React + Tailwind chat UI with Markdown rendering and code highlighting.

This is the finished, verified version -- type the lesson's own steps
yourself first; come back here to compare your output or see it run.

- `backend/` -- the FastAPI app from the Build lesson (conversations CRUD,
  streaming chat endpoint, multi-provider abstraction) plus token counting
  from the Deploy lesson
- `frontend/` -- the React + Vite chat UI from the Build lesson's Step 5,
  with a minimal sidebar (list/create/delete conversations) added so the
  app is actually usable end to end
- `docker-compose.yml` -- the two-service compose file from the Deploy lesson
- `backend/Dockerfile`, `frontend/Dockerfile` -- verified locally only; no
  cloud deployment was provisioned for this reference

## Setup

```bash
cp .env.example .env    # then add your ANTHROPIC_API_KEY / OPENAI_API_KEY
```

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.api:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev -- --port 5173
```

Open http://localhost:5173.

## Run with Docker Compose

```bash
docker compose up --build
```

Backend on http://localhost:8000, frontend on http://localhost:5173.

## Using a local model (no API key)

Install and start Ollama locally (`ollama pull llama3.2`), then create a
conversation with `"model": "ollama"`.
