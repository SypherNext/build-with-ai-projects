# Daily AI News Digest

Reference implementation for the "Daily AI News Digest" Mini Project in
Sypher's `build-with-ai` course. A CLI that fetches articles from three AI
RSS feeds, deduplicates overlapping stories, summarizes and ranks them with
Claude Haiku, and writes a clean Markdown digest file.

This is the finished, verified version -- type the lesson's own steps
yourself first; come back here to compare your output or see it run.

## Setup

```bash
python -m venv venv
source venv/bin/activate   # venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env       # then add your ANTHROPIC_API_KEY
```

## Run

```bash
python digest.py
```

The digest is written to `~/ai-digest/digest.md`.
