# AI Learning Platform

Reference implementation for the "AI Learning Platform" Production Project
in Sypher's `build-with-ai` course. A FastAPI backend (LearnAI) that
generates a full course -- lessons plus quizzes -- from a single topic with
Claude, serves adaptive quizzes that get harder or easier based on a
learner's performance, tracks per-user progress, and generates flashcards
on demand for review. Backed by SQLite.

This is the finished, verified version -- type the lesson's own steps
yourself first; come back here to compare your output or see it run.

- `app/` -- the FastAPI application from the Build and Deploy stages
  (`generator.py` course generation, `quiz.py` adaptive quizzes,
  `progress.py` completion tracking, `flashcards.py` flashcard generation,
  `cache.py` and `ratelimit.py` from the Deploy lesson's Production
  Hardening section, wired into `api.py`)
- `Dockerfile` -- builds the app into a container image (verified locally
  only; no cloud deployment was provisioned for this reference)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env        # then add your ANTHROPIC_API_KEY
```

## Run the API locally

```bash
uvicorn app.api:app --reload --port 8003
# then open http://localhost:8003/docs
```

## Build the Docker image locally

```bash
docker build -t ai-learning-platform .
docker run -p 8003:8003 --env-file .env ai-learning-platform
```
