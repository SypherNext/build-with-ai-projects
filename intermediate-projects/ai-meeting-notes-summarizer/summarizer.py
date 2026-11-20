"""AI Meeting Notes Summarizer -- turns a raw meeting transcript into a
structured Markdown summary (decisions, action items, open questions)."""

import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    print("Error: ANTHROPIC_API_KEY not set in .env")
    sys.exit(1)

import anthropic

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def detect_meeting_type(transcript: str) -> str:
    """Detect the meeting type from the transcript content."""
    keywords = {
        "standup": ["standup", "yesterday", "today", "blocker", "what did you"],
        "retro": ["retro", "sprint retrospective", "what went well", "start doing"],
        "planning": ["planning", "sprint planning", "estimate", "story points", "backlog"],
        "one-on-one": ["1:1", "one-on-one", "1-1", "career", "feedback"],
        "brainstorming": ["brainstorm", "ideate", "think of ideas", "what if"],
    }
    transcript_lower = transcript.lower()
    scores = {}
    for meeting_type, words in keywords.items():
        score = sum(1 for word in words if word in transcript_lower)
        if score > 0:
            scores[meeting_type] = score
    if not scores:
        return "general"
    return max(scores, key=scores.get)


PROMPT_TEMPLATES = {
    "standup": (
        "You are summarising a daily standup meeting. Extract the following:\n"
        "1. OVERVIEW: One sentence summarising the team's focus today.\n"
        "2. COMPLETED: What each person completed since last standup.\n"
        "3. PLANNED: What each person plans to do today.\n"
        "4. BLOCKERS: Any blockers raised, with owner.\n"
        "5. ACTION ITEMS: Specific follow-ups with owners.\n\n"
        "Format as Markdown with clear headings."
    ),
    "retro": (
        "You are summarising a sprint retrospective. Extract:\n"
        "1. OVERVIEW: One sentence on the retro focus.\n"
        "2. WENT WELL: Things the team agreed went well.\n"
        "3. TO IMPROVE: Things the team wants to change.\n"
        "4. ACTION ITEMS: Specific improvement actions with owners.\n"
        "5. TEAM MOOD: Overall sentiment (positive/mixed/negative).\n\n"
        "Format as Markdown with clear headings."
    ),
    "planning": (
        "You are summarising a sprint planning meeting. Extract:\n"
        "1. OVERVIEW: Sprint goal and scope.\n"
        "2. COMMITTED: Stories or tasks committed, with point estimates if available.\n"
        "3. CAPACITY: Team capacity and any availability notes.\n"
        "4. RISKS: Any risks or dependencies raised.\n"
        "5. ACTION ITEMS: Follow-ups with owners.\n\n"
        "Format as Markdown with clear headings."
    ),
    "one-on-one": (
        "You are summarising a one-on-one meeting. Extract:\n"
        "1. OVERVIEW: Main topics discussed.\n"
        "2. HIGHLIGHTS: Positive updates or achievements.\n"
        "3. CONCERNS: Any issues or concerns raised.\n"
        "4. CAREER: Career development discussions.\n"
        "5. ACTION ITEMS: Follow-ups with owners.\n\n"
        "Format as Markdown with clear headings."
    ),
    "general": (
        "You are summarising a meeting. Extract:\n"
        "1. OVERVIEW: One-paragraph executive summary.\n"
        "2. KEY DISCUSSION POINTS: The main topics discussed.\n"
        "3. DECISIONS: Any decisions made, with who made them.\n"
        "4. ACTION ITEMS: Specific follow-ups with owners.\n"
        "5. OPEN QUESTIONS: Items that need further discussion.\n\n"
        "Format as Markdown with clear headings."
    ),
}

PROMPT_TEMPLATES["brainstorming"] = (
    "You are summarising a brainstorming session. Extract:\n"
    "1. OVERVIEW: The problem or topic being brainstormed.\n"
    "2. IDEAS: A numbered list of all ideas generated.\n"
    "3. THEMES: Common themes or categories among the ideas.\n"
    "4. NEXT STEPS: Which ideas were selected for further exploration.\n"
    "5. ACTION ITEMS: Follow-ups with owners.\n\n"
    "Format as Markdown with clear headings."
)


def summarize_transcript(
    transcript: str,
    meeting_type: str = None,
    custom_context: str = None
) -> str:
    """Summarize a meeting transcript using the LLM."""
    if not meeting_type:
        meeting_type = detect_meeting_type(transcript)

    template = PROMPT_TEMPLATES.get(meeting_type, PROMPT_TEMPLATES["general"])

    system_prompt = (
        f"{template}\n\n"
        "Be specific: include names, numbers, and concrete details from the transcript. "
        "If a decision or action item has no clear owner, note that. "
        "Do not add information not present in the transcript."
    )

    user_message = f"Transcript:\n\n{transcript}"
    if custom_context:
        user_message = f"Context: {custom_context}\n\n{user_message}"

    response = client.messages.create(
        model="claude-haiku-5-5",
        max_tokens=2000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}]
    )

    summary = response.content[0].text
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    print(f"Processed {input_tokens} input tokens, {output_tokens} output tokens")

    return summary


def load_transcript(file_path: str) -> str:
    """Load a transcript from a text file."""
    path = Path(file_path)
    if not path.exists():
        print(f"Error: file not found: {file_path}")
        sys.exit(1)
    return path.read_text(encoding="utf-8")


def save_summary(summary: str, output_dir: str = "summaries") -> str:
    """Save the summary to a timestamped file."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_path / f"meeting_summary_{timestamp}.md"
    filename.write_text(summary, encoding="utf-8")
    print(f"Summary saved to: {filename}")
    return str(filename)


def main():
    print("=" * 50)
    print("  AI Meeting Notes Summarizer")
    print("=" * 50)

    source = input("\nEnter transcript text (T) or load from file (F)? ").strip().lower()

    if source == "f":
        file_path = input("Enter transcript file path: ").strip()
        transcript = load_transcript(file_path)
        print(f"Loaded {len(transcript)} characters from {file_path}")
    else:
        print("Paste the transcript below. Press Enter, then Ctrl+Z (Windows)")
        print("or Ctrl+D (macOS/Linux) on a blank line to finish:\n")
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        transcript = "\n".join(lines)

    if not transcript.strip():
        print("Error: no transcript provided")
        sys.exit(1)

    # Detect and show type
    meeting_type = detect_meeting_type(transcript)
    print(f"\nDetected meeting type: {meeting_type}")

    # Optional custom context
    context = input("Add custom context (optional, press Enter to skip): ").strip()
    if not context:
        context = None

    print("\nGenerating summary...\n")
    summary = summarize_transcript(transcript, meeting_type, context)
    print("\n" + "=" * 50)
    print(summary)
    print("=" * 50)

    # Save
    save = input("\nSave summary to file? (y/n): ").strip().lower()
    if save == "y":
        save_summary(summary)


if __name__ == "__main__":
    main()
