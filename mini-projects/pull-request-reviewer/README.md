# Pull Request Reviewer

Reference implementation for the "Pull Request Reviewer" Mini Project in
Sypher's `build-with-ai` course. A CLI that diffs your current git branch
against main/master and uses Claude Haiku to generate a structured
Markdown code review -- flagging logic errors, missing error handling,
hardcoded values, dead code, and style issues, each with a line number,
severity, and confidence rating.

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
python pr_review.py
```

Run it from inside a git repository whose current branch has diverged from
`main` (or `master`). It writes the full review to `review_report.md` and
prints a findings summary to stdout.
