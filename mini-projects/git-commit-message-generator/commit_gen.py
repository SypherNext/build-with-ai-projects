#!/usr/bin/env python3
"""Generate conventional commit messages from git diffs using Claude Haiku."""

import argparse
import os
import subprocess
import sys
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

MAX_ITERATIONS = int(os.environ.get("MAX_ITERATIONS", "5"))
MAX_TOKENS_PER_RUN = int(os.environ.get("MAX_TOKENS_PER_RUN", "10000"))

api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    print("Error: ANTHROPIC_API_KEY not found in .env file.")
    print("Copy .env.example to .env and add your key.")
    sys.exit(1)

client = Anthropic(api_key=api_key)

VALID_TYPES = [
    "feat", "fix", "docs", "style",
    "refactor", "perf", "test", "chore", "ci",
]


def read_git_diff(args: argparse.Namespace) -> str:
    """Read diff from stdin, a file, or git directly."""
    if args.diff_file:
        with open(args.diff_file, "r", encoding="utf-8") as f:
            return f.read()

    if not sys.stdin.isatty():
        return sys.stdin.read()

    # Try git diff --cached first, then git diff
    for cmd in [
        ["git", "diff", "--cached"],
        ["git", "diff"],
    ]:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.stdout.strip():
            return result.stdout

    print("No diff found. Make sure you are in a git repository with changes.")
    sys.exit(1)


def copy_to_clipboard(text: str) -> None:
    """Copy text to the system clipboard."""
    try:
        if sys.platform == "darwin":
            subprocess.run(["pbcopy"], input=text, text=True, check=True)
        elif sys.platform == "win32":
            subprocess.run(["clip"], input=text, text=True, check=True)
        else:
            subprocess.run(
                ["xclip", "-selection", "clipboard"],
                input=text, text=True, check=True,
            )
        print("Copied to clipboard.")
    except (subprocess.SubprocessError, FileNotFoundError):
        print("Could not copy to clipboard. Install xclip on Linux.")


def generate_commit_message(diff_text: str, commit_type: str | None = None) -> str:
    """Send diff to Claude Haiku and return a conventional commit message."""
    prompt_parts = [
        "You are a senior software engineer writing concise, accurate git commit messages.",
        "",
        "Generate a conventional commit message for the following code diff.",
        "",
    ]
    if commit_type:
        prompt_parts.append(f"The commit type must be: {commit_type}")
        prompt_parts.append("")

    prompt_parts.extend([
        "Format your response as:",
        "type(scope): short subject line (max 72 characters)",
        "",
        "Longer body explaining what changed and why.",
        "- Use bullet points for multiple changes if needed.",
        "- Keep the body under 80 characters per line.",
        "",
        "Valid types: feat, fix, docs, style, refactor, perf, test, chore, ci",
        "",
        "Diff:",
        diff_text,
    ])

    prompt = "\n".join(prompt_parts)

    response = client.messages.create(
        model="claude-haiku-5-5",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate conventional git commit messages with Claude Haiku",
    )
    parser.add_argument(
        "--type", "-t",
        choices=VALID_TYPES,
        help="Force a specific conventional commit type",
    )
    parser.add_argument(
        "--diff-file", "-f",
        help="Read diff from a file instead of stdin or git",
    )
    parser.add_argument(
        "--copy", "-c",
        action="store_true",
        help="Copy the generated message to clipboard",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    diff_text = read_git_diff(args)

    print(f"Read {len(diff_text)} characters of diff.")
    print("Generating commit message with Claude Haiku...\n")

    total_tokens = 0
    commit_message = ""

    for i in range(MAX_ITERATIONS):
        if total_tokens > MAX_TOKENS_PER_RUN:
            print(f"Token budget reached at iteration {i}.")
            print("Set MAX_TOKENS_PER_RUN in .env to increase.")
            break

        commit_message = generate_commit_message(diff_text, commit_type=args.type)
        print("--- Generated Commit Message ---")
        print(commit_message)
        print("---")
        break  # Single-pass for now

    if args.copy and commit_message:
        copy_to_clipboard(commit_message)


if __name__ == "__main__":
    main()
