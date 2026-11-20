# README Generator

Reference implementation for the "README Generator" Mini Project in Sypher's
`build-with-ai` course. A CLI tool that scans a local codebase directory and
generates a polished `README.md` automatically, using Claude Haiku.

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
python readme_gen.py /path/to/your/project --force
python readme_gen.py /path/to/your/project
```
