# Send Me New Job Listings

Reference implementation for the "Send Me New Job Listings" Mini Project in
Sypher's `build-with-ai` course. A Python script that fetches job listings
from a free RSS feed, filters them against your personal criteria using
Claude Haiku, and emails you a daily HTML digest via SMTP.

This is the finished, verified version -- type the lesson's own steps
yourself first; come back here to compare your output or see it run.

## Setup

```bash
python -m venv venv
source venv/bin/activate   # venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env       # then add your ANTHROPIC_API_KEY and SMTP settings
```

## Run

```bash
python job_tracker.py              # Fetch, rank, and email digest
python job_tracker.py --dry-run    # Fetch and rank only, no email
python job_tracker.py --profile    # Rebuild profile interactively
```

To run daily, schedule it with cron (macOS/Linux):

```
0 7 * * * cd ~/job-tracker && source venv/bin/activate && python job_tracker.py
```

On Windows, use Task Scheduler pointing to `venv\Scripts\python.exe` with the
script path as the argument.
