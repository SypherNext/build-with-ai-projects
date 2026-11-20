#!/usr/bin/env python3
"""AI Interview Coach — practice interviews with Claude Haiku."""

import json
import os
import sys
from dotenv import load_dotenv

load_dotenv()

MAX_ITERATIONS = int(os.environ.get("MAX_ITERATIONS", "50"))
MAX_TOKENS_PER_RUN = int(os.environ.get("MAX_TOKENS_PER_RUN", "4096"))

api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    print("Error: ANTHROPIC_API_KEY not found in .env file.")
    sys.exit(1)

from anthropic import Anthropic
from datetime import datetime
from pathlib import Path

client = Anthropic(api_key=api_key)

LOG_PATH = Path.home() / "interview-coach" / "session_log.json"

ROLES = {
    "1": {"name": "Software Engineer",  "style": "technical"},
    "2": {"name": "Product Manager",    "style": "product"},
    "3": {"name": "Data Scientist",     "style": "analytical"},
    "4": {"name": "Engineering Manager","style": "leadership"},
}


def select_role() -> dict:
    print("\n=== AI Interview Coach ===\n")
    print("Select your target role:\n")
    for key, role in ROLES.items():
        print(f"  {key}. {role['name']}")
    while True:
        choice = input("\nEnter number (1-4): ").strip()
        if choice in ROLES:
            return ROLES[choice]
        print("Invalid choice.")


def generate_questions(role: dict, count: int = 6) -> list[str]:
    """Generate interview questions using Claude Haiku."""
    response = client.messages.create(
        model="claude-haiku-5-5",
        max_tokens=MAX_TOKENS_PER_RUN,
        system=(
            f"You are a hiring manager. Generate {count} questions for a "
            f"{role['name']} position — 3 behavioral and 3 {role['style']}. "
            f"Output as a JSON array of strings."
        ),
        messages=[
            {"role": "user", "content": f"Generate {count} questions for {role['name']}."}
        ],
    )
    text = response.content[0].text.strip()
    if "[" in text:
        text = text[text.index("["):text.rindex("]") + 1]
    return json.loads(text)[:count]


def ask_question(question: str, num: int, total: int) -> str:
    """Display a question and collect the user's typed answer."""
    print(f"\n{'=' * 60}")
    print(f"Question {num} of {total}")
    print(f"{'=' * 60}\n{question}\n")
    print("Type your answer. Press Enter twice to finish:\n")
    lines = []
    while True:
        line = input()
        if line == "" and (not lines or lines[-1] == ""):
            if lines:
                lines.pop()
            break
        lines.append(line)
    return "\n".join(lines)


def evaluate_answer(question: str, answer: str, role: dict) -> dict:
    """Evaluate the user's answer and return a score with feedback."""
    response = client.messages.create(
        model="claude-haiku-5-5",
        max_tokens=MAX_TOKENS_PER_RUN,
        system=(
            "You are an expert interview coach. Return a JSON object with: "
            "score (0-100), star_used (bool), clarity (0-25), "
            "relevance (0-25), structure (0-25), impact (0-25), "
            "strengths (list), improvements (list), sample_answer (string)."
        ),
        messages=[{
            "role": "user",
            "content": f"Role: {role['name']}\nQuestion: {question}\n\nAnswer: {answer}\n\nEvaluate."
        }],
    )
    text = response.content[0].text.strip()
    if "{" in text:
        text = text[text.index("{"):text.rindex("}") + 1]
    return json.loads(text)


def display_feedback(ev: dict, num: int) -> None:
    """Print evaluation feedback to the terminal."""
    print(f"\n{'=' * 60}")
    print(f"Feedback for Question {num}")
    print(f"{'=' * 60}")
    score = ev["score"]
    bar = "█" * int(score / 100 * 50) + "░" * (50 - int(score / 100 * 50))
    print(f"\nOverall Score: {score}/100  [{bar}]")
    print(f"  Clarity: {ev['clarity']}/25 | Relevance: {ev['relevance']}/25")
    print(f"  Structure: {ev['structure']}/25 | Impact: {ev['impact']}/25")
    if ev.get("star_used"):
        print("  STAR Method: Used")
    print(f"\nStrengths:")
    for s in ev["strengths"]:
        print(f"  + {s}")
    print(f"\nAreas to Improve:")
    for imp in ev["improvements"]:
        print(f"  - {imp}")
    print(f"\nSample Strong Answer:\n  {ev['sample_answer']}")
    input("\nPress Enter to continue...")


def save_session(role_name: str, scores: list[int]) -> list[dict]:
    """Save session results to the JSON log file."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    session = {
        "date": datetime.now().isoformat(),
        "role": role_name,
        "scores": scores,
        "average": round(sum(scores) / len(scores), 1) if scores else 0,
    }
    history = []
    if LOG_PATH.exists():
        with open(LOG_PATH, "r") as f:
            history = json.load(f)
    history.append(session)
    with open(LOG_PATH, "w") as f:
        json.dump(history, f, indent=2)
    return history


def show_progress(history: list[dict]) -> None:
    """Display a progress table of recent sessions."""
    print(f"\n{'=' * 60}")
    print("Your Progress Over Time\n")
    print(f"{'Session':<10} {'Role':<20} {'Avg Score':<12} {'Date':<12}")
    print("-" * 60)
    for i, s in enumerate(history[-10:], max(1, len(history) - 9)):
        print(f"{i:<10} {s['role']:<20} {s['average']:<12.1f} {s['date'][:10]:<12}")
    if len(history) >= 2:
        lf = [s["average"] for s in history[-5:]]
        print(f"\nTrend (last 5): {'improving' if lf[-1] > lf[0] else 'needs work'}")
    print()


def main() -> None:
    role = select_role()
    print(f"\nPreparing questions for {role['name']}...")
    questions = generate_questions(role)
    total = len(questions)
    print(f"Starting interview with {total} questions.\n")

    scores = []
    total_tokens = 0
    for i, q in enumerate(questions, 1):
        if total_tokens > MAX_TOKENS_PER_RUN:
            print(f"Token budget reached. Increase MAX_TOKENS_PER_RUN in .env.")
            break
        answer = ask_question(q, i, total)
        print("\nEvaluating your answer...")
        ev = evaluate_answer(q, answer, role)
        total_tokens += 500
        display_feedback(ev, i)
        scores.append(ev["score"])

    print(f"\n{'=' * 60}")
    print("Session Complete!")
    print(f"{'=' * 60}")
    if scores:
        print(f"\nAverage: {sum(scores)/len(scores):.1f}/100")
        print(f"Best:    {max(scores):.1f}/100")
        print(f"Focus:   {min(scores):.1f}/100")

    history = save_session(role["name"], scores)
    show_progress(history)
    print("Good luck with your interviews!")


if __name__ == "__main__":
    main()
