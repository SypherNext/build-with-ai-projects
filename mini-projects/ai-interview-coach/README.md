# AI Interview Coach

Reference implementation for the "AI Interview Coach" Mini Project in
Sypher's `build-with-ai` course. A CLI that runs a mock interview for a
chosen role (Software Engineer, Product Manager, Data Scientist, or
Engineering Manager), asking Claude Haiku-generated questions, scoring your
typed answers on clarity, relevance, structure, and impact, and tracking
your average score across sessions in a local JSON log.

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
python interview_coach.py
```
