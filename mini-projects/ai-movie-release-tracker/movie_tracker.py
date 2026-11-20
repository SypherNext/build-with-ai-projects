#!/usr/bin/env python3
"""Fetch upcoming movies from TMDB and rank them with Claude Haiku."""

import os
import sys
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

MAX_ITERATIONS = int(os.environ.get("MAX_ITERATIONS", "10"))
MAX_TOKENS_PER_RUN = int(os.environ.get("MAX_TOKENS_PER_RUN", "10000"))

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
TMDB_API_KEY = os.environ.get("TMDB_API_KEY")

if not ANTHROPIC_API_KEY:
    print("Error: ANTHROPIC_API_KEY not found in .env file.")
    sys.exit(1)
if not TMDB_API_KEY:
    print("Error: TMDB_API_KEY not found in .env file.")
    print("Get a free key at themoviedb.org/settings/api")
    sys.exit(1)

TMDB_BASE = "https://api.themoviedb.org/3"
PROFILE_FILE = "taste_profile.json"

client = Anthropic(api_key=ANTHROPIC_API_KEY)


def fetch_upcoming(days_ahead: int = 60) -> list[dict]:
    """Fetch upcoming movie releases from TMDB."""
    import requests
    today = datetime.now().strftime("%Y-%m-%d")
    end = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

    url = f"{TMDB_BASE}/discover/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "primary_release_date.gte": today,
        "primary_release_date.lte": end,
        "sort_by": "popularity.desc",
        "page": 1,
    }
    print(f"Fetching upcoming movies from TMDB...")
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    movies = []
    for m in data.get("results", [])[:20]:
        movies.append({
            "id": m["id"],
            "title": m["title"],
            "overview": m.get("overview", ""),
            "release_date": m.get("release_date", ""),
            "vote_average": m.get("vote_average", 0),
            "genre_ids": m.get("genre_ids", []),
        })
    print(f"Found {len(movies)} upcoming movies.")
    return movies


def build_or_load_profile() -> dict:
    """Load existing profile or build one interactively."""
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "r") as f:
            return json.load(f)

    print("\nLet us build your movie taste profile.\n")
    profile = {
        "favorite_genres": input(
            "Favorite genres (comma-sep, e.g., sci-fi, thriller): "
        ).strip(),
        "favorite_directors": input(
            "Favorite directors (comma-sep): "
        ).strip(),
        "favorite_actors": input(
            "Favorite actors (comma-sep): "
        ).strip(),
        "moods": input(
            "Preferred moods (e.g., thought-provoking, funny, intense): "
        ).strip(),
        "disliked_genres": input(
            "Genres to avoid (comma-sep): "
        ).strip(),
    }
    with open(PROFILE_FILE, "w") as f:
        json.dump(profile, f, indent=2)
    print(f"Profile saved to {PROFILE_FILE}.")
    return profile


def score_movie(movie: dict, profile: dict) -> dict:
    """Ask Claude Haiku to score a movie based on the taste profile."""
    profile_text = f"""
Favorite genres: {profile['favorite_genres']}
Favorite directors: {profile['favorite_directors']}
Favorite actors: {profile['favorite_actors']}
Preferred moods: {profile['moods']}
Disliked genres: {profile['disliked_genres']}
"""
    prompt = f"""Given this taste profile:{profile_text}
Score this upcoming movie from 1-10 for how much the user would enjoy it.
Return JSON: {{"score": <int>, "reason": "<one-sentence reason>"}}

Movie: {movie['title']}
Overview: {movie['overview'][:300]}
Release: {movie['release_date']}
Rating: {movie['vote_average']}/10"""

    response = client.messages.create(
        model="claude-haiku-5-5",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text.strip()
    if "{" in text:
        text = text[text.index("{"):text.rindex("}") + 1]
    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        result = {"score": 5, "reason": "Could not parse rating."}
    return result


def filter_and_rank(movies: list[dict], profile: dict) -> list[dict]:
    """Score all movies and return them sorted by relevance."""
    scored = []
    total_tokens = 0
    for i, movie in enumerate(movies):
        if total_tokens > MAX_TOKENS_PER_RUN:
            print(f"  Token budget reached after {i} movies.")
            break
        result = score_movie(movie, profile)
        total_tokens += 500
        movie["recommendation_score"] = result["score"]
        movie["recommendation_reason"] = result["reason"]
        scored.append(movie)
        print(f"  [{result['score']}/10] {movie['title']}")
    scored.sort(key=lambda m: m["recommendation_score"], reverse=True)
    return scored


def display_watchlist(scored: list[dict]) -> None:
    """Print a formatted watchlist table."""
    print(f"\n{'=' * 70}")
    print("  YOUR PERSONALIZED WATCHLIST")
    print(f"{'=' * 70}\n")
    print(f"{'Score':<7} {'Title':<40} {'Release':<15}")
    print("-" * 70)
    for m in scored:
        bar = "★" * (m["recommendation_score"] // 2) + "☆" * (5 - m["recommendation_score"] // 2)
        print(f"{bar:<7} {m['title'][:38]:<40} {m['release_date']:<15}")
    print(f"\nTop Pick: {scored[0]['title']} ({scored[0]['recommendation_score']}/10)")
    print(f"  {scored[0]['recommendation_reason']}")


def save_watchlist(scored: list[dict]) -> str:
    """Save the ranked watchlist to a markdown file."""
    safe_date = datetime.now().strftime("%Y%m%d")
    filename = f"watchlist_{safe_date}.md"
    lines = [
        f"# Movie Watchlist — {datetime.now().strftime('%B %d, %Y')}",
        "",
        f"_{len(scored)} upcoming movies ranked for your taste._",
        "",
        "| Score | Title | Release | Reason |",
        "|-------|-------|---------|--------|",
    ]
    for m in scored:
        stars = "★" * (m["recommendation_score"] // 2) + "☆" * (5 - m["recommendation_score"] // 2)
        lines.append(
            f"| {stars} | {m['title']} | {m['release_date']} "
            f"| {m['recommendation_reason']} |"
        )
    content = "\n".join(lines)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\nWatchlist saved to: {filename}")
    return filename


def main() -> None:
    profile = build_or_load_profile()
    movies = fetch_upcoming(60)

    print("\nScoring movies with Claude Haiku...\n")
    scored = filter_and_rank(movies, profile)

    display_watchlist(scored)

    save = input("\nSave watchlist to file? (y/n): ").strip().lower()
    if save.startswith("y"):
        save_watchlist(scored)

    print("\nDone! Check back next week for new releases.")
    print("Tip: Schedule this script with cron or Task Scheduler for weekly updates.")


if __name__ == "__main__":
    main()
