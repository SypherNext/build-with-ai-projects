# Email Me New AI Research Papers

Reference implementation for the "Email Me New AI Research Papers" Mini
Project in Sypher's `build-with-ai` course. A Python script that fetches AI
papers from the arXiv API, summarizes them with Claude Haiku based on your
interests, and emails a daily curated digest via smtplib.

This is the finished, verified version -- type the lesson's own steps
yourself first; come back here to compare your output or see it run.

## Setup

```bash
python -m venv venv
source venv/bin/activate   # venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env       # then add your ANTHROPIC_API_KEY and email/SMTP settings
```

For Gmail with 2FA, use an app password for `EMAIL_PASSWORD`.

## Run

```bash
python research_digest.py
```

To run daily, add a cron job: `0 7 * * * cd ~/research-digest && venv/bin/python research_digest.py`

On Windows, use Task Scheduler to trigger `venv/Scripts/python.exe` with
`research_digest.py` as the argument.
