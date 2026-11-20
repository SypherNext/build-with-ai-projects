# Travel Itinerary Planner

Reference implementation for the "Travel Itinerary Planner" Mini Project in
Sypher's `build-with-ai` course. A CLI tool where you describe your
destination, dates, and preferences, and Claude Haiku generates a complete
day-by-day itinerary with activities, meal suggestions, and timing.

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
python travel_planner.py
```

Enter your destination, dates, interests, and budget level when prompted.
The tool prints the generated itinerary and offers to save it to a
timestamped markdown file in the current directory.
