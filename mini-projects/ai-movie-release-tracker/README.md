# AI Movie Release Tracker

Reference implementation for the "AI Movie Release Tracker" Mini Project in
Sypher's `build-with-ai` course. A CLI that fetches upcoming movie releases
from TMDB, scores each one against your personal taste profile with Claude
Haiku, and prints (and optionally saves) a ranked watchlist.

This is the finished, verified version -- type the lesson's own steps
yourself first; come back here to compare your output or see it run.

## Setup

```bash
python -m venv venv
source venv/bin/activate   # venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env       # then add your ANTHROPIC_API_KEY and TMDB_API_KEY
```

## Run

```bash
python movie_tracker.py
```

On first run you'll be prompted to build a taste profile (favorite genres,
directors, actors, moods, and genres to avoid) -- it's saved to
`taste_profile.json` and reused on later runs. The script fetches upcoming
TMDB releases, scores them with Claude Haiku, prints a ranked watchlist with
star ratings, and offers to save it to a `watchlist_YYYYMMDD.md` file.
Schedule it weekly with cron (macOS/Linux) or Task Scheduler (Windows) for
fresh recommendations.
