#!/usr/bin/env python3
"""Fetch AI papers from arXiv, filter with Claude, and email a digest."""

import html, json, os, smtplib, sys, time
from dataclasses import dataclass, field
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
from anthropic import Anthropic
import feedparser

load_dotenv()

MAX_ITERATIONS = int(os.environ.get("MAX_ITERATIONS", "5"))
MAX_TOKENS_PER_RUN = int(os.environ.get("MAX_TOKENS_PER_RUN", "50000"))

api_key = os.environ.get("ANTHROPIC_API_KEY")
email_addr = os.environ.get("EMAIL_ADDRESS")
email_pass = os.environ.get("EMAIL_PASSWORD")
smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
smtp_port = int(os.environ.get("SMTP_PORT", "587"))

missing = [k for k, v in [("ANTHROPIC_API_KEY", api_key), ("EMAIL_ADDRESS", email_addr), ("EMAIL_PASSWORD", email_pass)] if not v]
if missing:
    print(f"Missing: {', '.join(missing)}")
    sys.exit(1)

client = Anthropic(api_key=api_key)

ARXIV_CATEGORIES = ["cs.AI", "cs.LG", "cs.CL"]
ARXIV_BASE_URL = "https://rss.arxiv.org/rss"

INTEREST_PROFILE = {
    "keywords": ["reinforcement learning from human feedback", "RLHF", "chain-of-thought", "constitutional AI", "mechanistic interpretability", "sparse autoencoders", "prompt optimization", "tool use", "retrieval augmented generation", "safety alignment"],
    "authors": [],
    "topics": ["alignment and safety", "interpretability", "reasoning and planning", "efficient fine-tuning"],
    "min_relevance_score": 5,
}

SYSTEM_PROMPT = "Evaluate AI papers for relevance (1-10). Write a two-sentence summary. JSON only."


@dataclass
class Paper:
    arxiv_id: str
    title: str
    abstract: str
    link: str
    published: str
    authors: list[str] = field(default_factory=list)
    relevance_score: int = 1
    claude_summary: str = ""


def fetch_papers(categories, max_results=20):
    papers = []
    for cat in categories:
        url = f"{ARXIV_BASE_URL}/{cat}"
        print(f"Fetching {cat}...")
        feed = feedparser.parse(url)
        for entry in feed.entries[:max_results]:
            papers.append(Paper(arxiv_id=entry.get("id", ""), title=entry.get("title", "").replace("\n", " ").strip(), abstract=entry.get("summary", "").replace("\n", " ").strip(), link=entry.get("link", ""), published=entry.get("published", ""), authors=[a.get("name", "") for a in entry.get("authors", [])]))
        time.sleep(1)
    print(f"Fetched {len(papers)} papers.")
    return papers


def filter_and_summarize(papers, profile):
    profile_text = f"Keywords: {', '.join(profile['keywords'])}\nTopics: {', '.join(profile['topics'])}\n"
    scored, total_tokens = [], 0
    for paper in papers:
        if total_tokens > MAX_TOKENS_PER_RUN:
            break
        try:
            resp = client.messages.create(model="claude-haiku-5-5", max_tokens=300, system=SYSTEM_PROMPT, messages=[{"role": "user", "content": f"{profile_text}\nTitle: {paper.title}\nAbstract: {paper.abstract}\n"}])
            total_tokens += resp.usage.input_tokens + resp.usage.output_tokens
            result = json.loads(resp.content[0].text)
            paper.relevance_score = result.get("relevance_score", 1)
            paper.claude_summary = result.get("summary", paper.abstract[:200])
            if paper.relevance_score >= profile["min_relevance_score"]:
                scored.append(paper)
                print(f"  [{paper.relevance_score}/10] {paper.title[:60]}...")
        except Exception:
            continue
    scored.sort(key=lambda p: p.relevance_score, reverse=True)
    return scored


def build_html_digest(papers, profile):
    # Paper titles/authors/summaries come from arXiv feeds and Claude's
    # output -- both untrusted as far as HTML goes -- so every interpolated
    # value is escaped, and only an http(s) link is ever turned into an <a>.
    def safe_link(url: str) -> str:
        return url if url.startswith(("http://", "https://")) else "#"

    rows = "".join(
        f'<tr><td style="padding:8px;text-align:center;font-size:18px;">{html.escape(str(p.relevance_score))}/10</td>'
        f'<td style="padding:8px;"><a href="{html.escape(safe_link(p.link), quote=True)}" style="font-weight:600;color:#1a73e8;">{html.escape(p.title)}</a>'
        f'<br><small>{html.escape(", ".join(p.authors[:4]))}</small>'
        f'<p style="margin:6px 0;font-size:14px;">{html.escape(p.claude_summary)}</p></td></tr>'
        for p in papers
    )
    badges = "".join(
        f'<span style="display:inline-block;background:#e8f0fe;border-radius:12px;padding:2px 10px;margin:2px;font-size:12px;">{html.escape(kw)}</span>'
        for kw in profile["keywords"][:8]
    )
    return f"""<html><body style="font-family:sans-serif;max-width:640px;margin:0 auto;padding:20px;">
<div style="border-bottom:2px solid #1a73e8;padding-bottom:12px;margin-bottom:20px;"><h1 style="font-size:22px;margin:0;">AI Research Digest</h1><p style="color:#666;">Curated from arXiv cs.AI, cs.LG, cs.CL</p></div>
<div style="margin-bottom:20px;"><strong>Keywords:</strong><br>{badges}</div>
<table style="width:100%;border-collapse:collapse;"><thead><tr style="background:#f8f9fa;"><th style="padding:8px;text-align:center;width:60px;">Score</th><th style="padding:8px;text-align:left;">Paper</th></tr></thead><tbody>{rows}</tbody></table>
<p style="color:#999;font-size:11px;margin-top:20px;border-top:1px solid #ddd;padding-top:12px;">Generated by research_digest.py with Claude Haiku.</p></body></html>"""


def send_email(html_body, paper_count):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"AI Research Digest -- {paper_count} papers today"
    msg["From"] = msg["To"] = email_addr
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    print(f"Connecting to {smtp_server}:{smtp_port}...")
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(email_addr, email_pass)
        server.send_message(msg)
    print("Email sent.")


def main():
    print("=" * 50 + "\nAI Research Digest\n" + "=" * 50)
    papers = fetch_papers(ARXIV_CATEGORIES, 20)
    print("\nFiltering with Claude Haiku...")
    scored = filter_and_summarize(papers, INTEREST_PROFILE)
    print(f"\nResults: {len(scored)} relevant papers")
    if not scored:
        print("No papers met the threshold. Try broader keywords.")
        return
    for p in scored:
        print(f"\n[{p.relevance_score}/10] {p.title}\n  {p.claude_summary}")
    print("\nSending email digest...")
    send_email(build_html_digest(scored, INTEREST_PROFILE), len(scored))
    print("Done. Check your inbox.")


if __name__ == "__main__":
    main()
