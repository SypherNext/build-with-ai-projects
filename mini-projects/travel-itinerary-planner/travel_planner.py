#!/usr/bin/env python3
"""Travel Itinerary Planner -- generate day-by-day itineraries with AI."""

import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import anthropic
from anthropic import Anthropic

load_dotenv()

api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    print("Error: ANTHROPIC_API_KEY not found in .env file.")
    sys.exit(1)

MODEL_NAME = "claude-haiku-5-5"
MAX_TOKENS_PER_RUN = 4096
MAX_ITERATIONS = 3


def validate_date(date_str: str) -> bool:
    """Check if a date string is valid YYYY-MM-DD format."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def collect_preferences() -> dict:
    """Gather trip details from user input with validation."""
    print("=" * 50)
    print("  TRAVEL ITINERARY PLANNER")
    print("=" * 50)

    destination = input("Destination: ").strip()
    while not destination:
        destination = input("Destination (required): ").strip()

    start_date = input("Start date (YYYY-MM-DD): ").strip()
    while start_date and not validate_date(start_date):
        start_date = input("Invalid format. Use YYYY-MM-DD: ").strip()

    end_date = input("End date (YYYY-MM-DD): ").strip()
    while end_date and not validate_date(end_date):
        end_date = input("Invalid format. Use YYYY-MM-DD: ").strip()

    interests = input(
        "Interests (e.g., museums, food, hiking): "
    ).strip()
    if not interests:
        interests = "general sightseeing"

    budget = input(
        "Budget level (budget / mid-range / luxury): "
    ).strip().lower()
    if budget not in ("budget", "mid-range", "luxury", ""):
        budget = "mid-range"
    elif not budget:
        budget = "mid-range"

    return {
        "destination": destination,
        "start_date": start_date,
        "end_date": end_date,
        "interests": interests,
        "budget": budget,
    }


def build_itinerary_prompt(prefs: dict) -> str:
    """Build a structured prompt for Claude Haiku to generate an itinerary."""
    num_days = "unknown number of"
    if prefs["start_date"] and prefs["end_date"]:
        try:
            start = datetime.strptime(
                prefs["start_date"], "%Y-%m-%d"
            )
            end = datetime.strptime(
                prefs["end_date"], "%Y-%m-%d"
            )
            days = (end - start).days
            if days > 0:
                num_days = f"{days}"
        except ValueError:
            pass

    prompt = f"""You are an expert travel planner with deep knowledge of
destinations worldwide. Create a detailed day-by-day itinerary based on
the following preferences.

Destination: {prefs['destination']}
Trip length: {num_days} days
Travel dates: {prefs['start_date']} to {prefs['end_date']}
Interests: {prefs['interests']}
Budget level: {prefs['budget']}

Requirements:
1. Use one ### heading per day (### Day 1, ### Day 2, etc.)
2. For each day include: **Morning** with start time, **Lunch** suggestion,
   **Afternoon** activities, **Dinner** suggestion, **Transit** estimates
3. Include descriptions and estimated costs for attractions
4. Max 3 major activities per day for realistic pacing
5. Account for typical opening hours
6. Include a Packing Tip and a Local Custom note at the end

Format as clean Markdown with bullet lists and bold labels."""
    return prompt


def generate_itinerary(prompt: str) -> str:
    """Send the prompt to Claude Haiku and return the itinerary text."""
    client = Anthropic(api_key=api_key)

    try:
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=MAX_TOKENS_PER_RUN,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )
        return response.content[0].text
    except anthropic.APIError as e:
        print(f"API error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise


def format_itinerary_output(raw_text: str, destination: str) -> str:
    """Clean up the generated itinerary into a polished markdown document."""
    lines = raw_text.strip().split("\n")
    cleaned = []
    today = datetime.now().strftime("%B %d, %Y")
    cleaned.append(f"# Travel Itinerary: {destination}")
    cleaned.append(f"")
    cleaned.append(f"_Generated on {today}_")
    cleaned.append(f"")
    cleaned.append(f"---")
    cleaned.append(f"")
    for line in lines:
        if line.strip().startswith("# "):
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


def save_itinerary(content: str, destination: str) -> str:
    """Save the itinerary to a file and return the file path."""
    safe_name = destination.lower().replace(" ", "_")
    today = datetime.now().strftime("%Y%m%d")
    filename = f"itinerary_{safe_name}_{today}.md"
    filepath = Path(filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return str(filepath)


def print_itinerary(content: str) -> None:
    """Display the itinerary in the terminal with a clear header."""
    print()
    print("=" * 60)
    print("  YOUR CUSTOM ITINERARY")
    print("=" * 60)
    print()
    print(content)
    print()
    print("=" * 60)


def main():
    prefs = collect_preferences()

    print()
    print("Building your personalized itinerary...")
    print(f"Contacting Claude Haiku with {prefs['destination']} preferences...")
    print()

    prompt = build_itinerary_prompt(prefs)

    for attempt in range(MAX_ITERATIONS):
        try:
            raw_itinerary = generate_itinerary(prompt)
        except Exception as e:
            print(f"Failed: {e}")
            if attempt < MAX_ITERATIONS - 1:
                continue
            else:
                sys.exit(1)

        formatted = format_itinerary_output(
            raw_itinerary, prefs["destination"]
        )
        print_itinerary(formatted)

        save_choice = input(
            "Save this itinerary to a file? (y/n): "
        ).strip().lower()
        if save_choice.startswith("y"):
            filepath = save_itinerary(
                formatted, prefs["destination"]
            )
            print(f"Itinerary saved to: {filepath}")
        else:
            print("You can generate a new one anytime.")
        break


if __name__ == "__main__":
    main()
