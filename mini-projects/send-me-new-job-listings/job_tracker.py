#!/usr/bin/env python3
"""Fetch, filter, and email job listings using Claude Haiku.

Usage:
    python job_tracker.py              # Fetch, rank, and email digest
    python job_tracker.py --dry-run    # Fetch and rank only, no email
    python job_tracker.py --profile    # Rebuild profile interactively
"""

import argparse
import html
import json
import os
import smtplib
import sys
import email.utils
from datetime import datetime, timezone
from typing import Any
from dotenv import load_dotenv
from anthropic import Anthropic
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

load_dotenv()

MAX_ITERATIONS = int(os.environ.get("MAX_ITERATIONS", "5"))
MAX_TOKENS_PER_RUN = int(os.environ.get("MAX_TOKENS_PER_RUN", "10000"))

api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    print("Error: ANTHROPIC_API_KEY not found in .env file.")
    sys.exit(1)

client = Anthropic(api_key=api_key)
PROFILE_FILE = "profile.json"


def fetch_jobs() -> list[dict[str, Any]]:
    import feedparser
    url = "https://jooble.org/Jobs/rss?keywords=python+developer&location="
    print(f"Fetching jobs from: {url}")
    feed = feedparser.parse(url)
    if feed.bozo and not feed.entries:
        return []
    jobs = []
    for entry in feed.entries[:30]:
        company = (entry.get("source", {}).get("title", "Unknown")
                   if hasattr(entry, "source") and entry.source
                   else "Unknown company")
        jobs.append({
            "title": entry.get("title", ""),
            "company": company,
            "location": entry.get("location", ""),
            "description": entry.get("summary", ""),
            "link": entry.get("link", ""),
            "published": entry.get("published", ""),
        })
    print(f"Found {len(jobs)} listings.")
    return jobs


def build_or_load_profile(force: bool = False) -> dict[str, Any]:
    if not force and os.path.exists(PROFILE_FILE):
        print(f"Loading profile from {PROFILE_FILE}.")
        with open(PROFILE_FILE) as f:
            return json.load(f)
    print("Set up your job search profile.\n")
    profile = {
        "skills": [s.strip() for s in input("Skills (comma-sep): ").split(",") if s.strip()],
        "preferred_location": input("Location (or 'remote'): ").strip(),
        "min_salary": int(input("Min salary: ").strip() or "0"),
        "job_type": input("Job type: ").strip(),
        "avoid_keywords": [k.strip() for k in input("Avoid keywords: ").split(",") if k.strip()],
        "max_years_experience": int(input("Max experience years: ").strip() or "99"),
    }
    with open(PROFILE_FILE, "w") as f:
        json.dump(profile, f, indent=2)
    print(f"Profile saved.")
    return profile


def rank_jobs(jobs: list[dict[str, Any]], profile: dict[str, Any]) -> list[dict[str, Any]]:
    if not jobs:
        return jobs
    summary = (
        f"Skills: {', '.join(profile['skills']) or 'any'}\n"
        f"Location: {profile['preferred_location'] or 'any'}\n"
        f"Min salary: ${profile['min_salary']:,}\n"
        f"Type: {profile['job_type'] or 'any'}\n"
        f"Avoid: {', '.join(profile['avoid_keywords']) or 'none'}\n"
        f"Max exp: {profile['max_years_experience']}yr"
    )
    text = "".join(
        f"--- Job {i} ---\nTitle: {j['title']}\nCompany: {j['company']}\n"
        f"Location: {j['location']}\n{j['description'][:500]}\n\n"
        for i, j in enumerate(jobs, 1)
    )
    prompt = (
        f"Score jobs 1-10 for this profile:\n{summary}\n\n{text}\n"
        'Return JSON: {"1": {"score": 8, "reason": "..."}}'
    )
    response = client.messages.create(
        model="claude-haiku-5-5", max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = "".join(raw.splitlines()[1:-1])
    try:
        scores = json.loads(raw)
    except json.JSONDecodeError:
        for job in jobs:
            job["score"] = 5
            job["reason"] = "Unranked"
        return jobs
    for i, job in enumerate(jobs, 1):
        e = scores.get(str(i), {})
        job["score"] = e.get("score", 1)
        job["reason"] = e.get("reason", "No match")
    jobs.sort(key=lambda j: j["score"], reverse=True)
    return jobs


def send_email_digest(ranked_jobs: list[dict[str, Any]]) -> None:
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USERNAME", "")
    smtp_pass = os.environ.get("SMTP_PASSWORD", "")
    from_email = os.environ.get("FROM_EMAIL", smtp_user)
    to_email = os.environ.get("TO_EMAIL", smtp_user)
    if not smtp_user or not smtp_pass:
        print("SMTP not configured. Skipping email.")
        return
    today = datetime.now(timezone.utc).strftime("%A, %B %d, %Y")
    top = ranked_jobs[:10]
    # Job titles/companies/scores come from an RSS feed and Claude's own
    # output -- both untrusted as far as HTML goes -- so every interpolated
    # value is escaped before it goes into the email body.
    rows = "".join(
        f"<tr><td><strong>{html.escape(str(j['title']))}</strong><br><span>{html.escape(str(j['company']))}</span></td>"
        f"<td><span>{html.escape(str(j['score']))}/10</span></td>"
        f"<td>{html.escape(str(j.get('reason', '')))}</td></tr>"
        for j in top if j["score"] >= 5
    )
    html_body = f"<html><body><h1>Daily Job Digest</h1><p>{today}</p><table>{rows}</table></body></html>"
    text = f"Daily Job Digest -- {today}\n\n" + "\n".join(
        f"[{j['score']}/10] {j['title']}" for j in top
    )
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Your Daily Job Digest -- {today}"
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Date"] = email.utils.formatdate(localtime=True)
    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html_body, "html"))
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(from_email, [to_email], msg.as_string())
    print(f"Digest sent to {to_email}.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Job tracker with Claude Haiku.")
    parser.add_argument("--dry-run", action="store_true", help="Skip email")
    parser.add_argument("--profile", action="store_true", help="Rebuild profile")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    jobs = fetch_jobs()
    if not jobs:
        sys.exit(1)
    profile = build_or_load_profile(force=args.profile)
    print(f"Ranking {len(jobs)} jobs with Claude Haiku...\n")
    for _ in range(MAX_ITERATIONS):
        ranked = rank_jobs(jobs, profile)
    with open("ranked_jobs.json", "w") as f:
        json.dump(ranked, f, indent=2)
    for job in ranked[:5]:
        print(f"  {job['score']}/10 — {job['title']}")
    if not args.dry_run:
        send_email_digest(ranked)
    else:
        print("[Dry run] No email sent.")


if __name__ == "__main__":
    main()
