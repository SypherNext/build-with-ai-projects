#!/usr/bin/env python3
"""Analyze a git branch's diff and generate structured code review comments
using Claude Haiku."""

import json
import os
import re
import subprocess
import sys
from typing import Any

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ["ANTHROPIC_API_KEY"]
MODEL = "claude-haiku-5-5"

# Spend guards
MAX_ITERATIONS = 3
MAX_TOKENS_PER_RUN = 4096


def get_current_branch() -> str:
    """Return the name of the current git branch."""
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def get_base_branch() -> str:
    """Detect the base branch: prefer main, fall back to master."""
    for candidate in ["main", "master"]:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", candidate],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return candidate
    sys.exit("Error: no base branch (main or master) found.")


def get_diff(base_branch: str) -> str:
    """Return the git diff between base_branch and the current branch."""
    result = subprocess.run(
        ["git", "diff", base_branch + "...HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


REVIEW_PROMPT = """You are a senior code reviewer. Review the following git diff and provide structured feedback.

For each file in the diff, analyze it for these categories:
1. LOGIC_ERRORS — potential bugs or incorrect assumptions
2. ERROR_HANDLING — missing try/except, unchecked edge cases
3. HARDCODED_VALUES — magic numbers or strings that should be configurable
4. DEAD_CODE — unused imports, unreachable branches, commented-out code
5. STYLE_ISSUES — violations of PEP 8 or Pythonic conventions

Return your analysis as valid JSON with this exact structure:
{
  "files": [
    {
      "file_path": "src/app.py",
      "findings": [
        {
          "line": 12,
          "category": "ERROR_HANDLING",
          "severity": "high",
          "message": "raise ValueError(\"data cannot be None\") on line 12 lacks a try/except wrapper — a None value from upstream will crash the request handler.",
          "confidence": 0.85
        }
      ]
    }
  ],
  "summary": {
    "total_files": 1,
    "total_findings": 1,
    "high_severity_count": 1,
    "medium_severity_count": 0,
    "low_severity_count": 0
  }
}

Guidelines:
- line must be an integer (0 if the finding applies to the whole file)
- severity must be "high", "medium", or "low"
- confidence must be a float between 0.0 and 1.0
- Only report actual issues — do not invent problems
- If the file has no issues, include it with an empty findings list

Here is the diff:

```
__DIFF_CONTENT__
```
"""


def parse_review_response(response_text: str) -> dict[str, Any]:
    """Extract and parse the JSON review from Claude's response."""
    # Try to extract JSON from code fence or raw text
    json_match = re.search(
        r"```(?:json)?\s*\n?(\{.*?\})\n?\s*```",
        response_text,
        re.DOTALL,
    )
    if json_match:
        raw = json_match.group(1)
    else:
        raw = response_text.strip()

    return json.loads(raw)


def generate_report(data: dict[str, Any]) -> str:
    """Convert the parsed review data into a Markdown report."""
    severity_colors = {
        "high": "🔴",
        "medium": "🟡",
        "low": "🟢",
    }

    lines = ["# Pull Request Review Report\n"]
    summary = data.get("summary", {})
    lines.append("## Summary")
    lines.append(f"- Files reviewed: {summary.get('total_files', 0)}")
    lines.append(f"- Total findings: {summary.get('total_findings', 0)}")
    lines.append(f"- High severity:   {summary.get('high_severity_count', 0)}")
    lines.append(f"- Medium severity: {summary.get('medium_severity_count', 0)}")
    lines.append(f"- Low severity:    {summary.get('low_severity_count', 0)}")
    lines.append("")

    for file_entry in data.get("files", []):
        file_path = file_entry["file_path"]
        findings = file_entry.get("findings", [])
        lines.append(f"## {file_path}")
        if not findings:
            lines.append("No issues found.")
            lines.append("")
            continue
        for f in findings:
            icon = severity_colors.get(f["severity"], "⚪")
            line_num = f.get("line", 0)
            category = f["category"]
            message = f["message"]
            confidence = f.get("confidence", 0.0)
            confidence_label = (
                "High" if confidence >= 0.7
                else "Medium" if confidence >= 0.4
                else "Low"
            )
            lines.append(
                f'{icon} **Line {line_num}** — {category} '
                f'(Severity: {f["severity"]}, Confidence: {confidence_label})'
            )
            lines.append(f"  {message}")
            lines.append("")
        lines.append("---")

    return "\n".join(lines)


def review_diff(diff_content: str) -> str:
    """Send the diff to Claude and return the raw response text."""
    if not diff_content.strip():
        return json.dumps({
            "files": [],
            "summary": {
                "total_files": 0,
                "total_findings": 0,
                "high_severity_count": 0,
                "medium_severity_count": 0,
                "low_severity_count": 0,
            },
        })

    client = Anthropic(api_key=API_KEY)
    # .replace(), not .format() -- the prompt's own JSON schema example is
    # full of literal { } characters that .format() would try to parse as
    # replacement fields.
    prompt = REVIEW_PROMPT.replace("__DIFF_CONTENT__", diff_content)

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS_PER_RUN,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def main() -> None:
    iteration = 0
    while iteration < MAX_ITERATIONS:
        try:
            current_branch = get_current_branch()
            base_branch = get_base_branch()
            print(f"Reviewing branch: {current_branch}")
            print(f"Against base:     {base_branch}")
            print("Fetching diff...")
            diff = get_diff(base_branch)
            print(f"Diff is {len(diff)} characters.")
            if not diff:
                print("No changes found. The branch is up to date with "
                      f"{base_branch}.")
                return
            print("Sending for review...")
            raw_response = review_diff(diff)
            print("Parsing response...")
            review_data = parse_review_response(raw_response)
            report = generate_report(review_data)
            output_path = "review_report.md"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"Review report written to {output_path}")

            # Print a quick summary to stdout
            summary = review_data.get("summary", {})
            print(f"\nFindings: {summary.get('total_findings', 0)} "
                  f"(High: {summary.get('high_severity_count', 0)}, "
                  f"Medium: {summary.get('medium_severity_count', 0)}, "
                  f"Low: {summary.get('low_severity_count', 0)})")
            return
        except Exception as e:
            iteration += 1
            print(f"Error (attempt {iteration}/{MAX_ITERATIONS}): {e}",
                  file=sys.stderr)
            if iteration >= MAX_ITERATIONS:
                print("Max retries reached. Exiting.", file=sys.stderr)
                sys.exit(1)


if __name__ == "__main__":
    main()
