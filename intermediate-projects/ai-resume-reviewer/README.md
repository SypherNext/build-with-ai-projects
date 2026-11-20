# AI Resume Reviewer

Reference implementation for the "AI Resume Reviewer" Intermediate Project in
Sypher's `build-with-ai` course. Analyses a resume against a job description
across five scored dimensions (skills, experience, achievements, keywords,
format) using Claude Haiku, and produces a structured Markdown report with
an ATS fit score, gaps, and suggestions.

This is the finished, verified version -- type the lesson's own steps
yourself first; come back here to compare your output or see it run.

- `reviewer.py` -- the CLI tool from the Build lesson (interactive resume-vs-job-description analysis)
- `app.py` -- the FastAPI web version from the Deploy stage (paste or upload a resume, get a report in the browser)
- `Dockerfile` -- builds `app.py` into a container image (verified locally only; no cloud deployment was provisioned for this reference)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env        # then add your ANTHROPIC_API_KEY
```

## Run the CLI

```bash
python reviewer.py
```

Use the included `sample_resume.txt` and `sample_job_desc.txt` as quick test
inputs, or point it at your own files.

## Run the web app locally

```bash
uvicorn app:app --reload
# then open http://localhost:8000
```

## Build the Docker image locally

```bash
docker build -t ai-resume-reviewer .
docker run -p 8000:8000 --env-file .env ai-resume-reviewer
```
