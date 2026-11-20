import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import feedparser
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

# ---------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------
RSS_FEEDS = [
    "https://huggingface.co/api/daily_papers?format=atom",
    "https://blog.google/technology/ai/rss/",
    "https://www.anthropic.com/news/rss.xml",
]

OUTPUT_DIR = Path.home() / "ai-digest"
MAX_ARTICLES = 20
MAX_SUMMARY_TOKENS = 300
MODEL_NAME = "claude-haiku-5-5"

# Spend guard rails
MAX_ITERATIONS = 50
MAX_TOKENS_PER_RUN = 50000


def fetch_feeds(feeds: List[str]) -> List[Dict]:
    """Fetch all articles from a list of RSS feeds."""
    articles = []
    for url in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:MAX_ARTICLES]:
                articles.append({
                    "title": entry.get("title", "Untitled"),
                    "url": entry.get("link", ""),
                    "summary": entry.get("summary", ""),
                    "published": entry.get("published", ""),
                    "source": url,
                })
            print(f"  Fetched {len(feed.entries[:MAX_ARTICLES])} articles from {url}")
        except Exception as e:
            print(f"  Error fetching {url}: {e}")
    return articles


def normalize_url(url: str) -> str:
    """Strip trailing slashes and query params for comparison."""
    return url.rstrip("/").split("?")[0].split("#")[0]


def title_similarity(t1: str, t2: str) -> float:
    """Simple word-overlap similarity for deduplication."""
    words1 = set(t1.lower().split())
    words2 = set(t2.lower().split())
    if not words1 or not words2:
        return 0.0
    intersection = words1 & words2
    union = words1 | words2
    return len(intersection) / len(union)


def deduplicate(articles: List[Dict], threshold: float = 0.6) -> List[Dict]:
    """Remove duplicates by URL and by title similarity."""
    seen_urls = set()
    seen_titles = []
    unique = []
    for article in articles:
        norm_url = normalize_url(article["url"])
        if norm_url in seen_urls:
            continue
        is_duplicate_title = any(
            title_similarity(article["title"], t) > threshold
            for t in seen_titles
        )
        if is_duplicate_title:
            continue
        seen_urls.add(norm_url)
        seen_titles.append(article["title"])
        unique.append(article)
    return unique


anthropic_client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def summarize_article(article: Dict) -> str:
    """Summarize a single article using Claude Haiku."""
    prompt = f"""You are an AI news curator. Summarize the following article in one paragraph (under {MAX_SUMMARY_TOKENS} tokens).
Include what happened, why it matters for AI engineers, and who should care.

Title: {article["title"]}
Content: {article["summary"]}
"""
    response = anthropic_client.messages.create(
        model=MODEL_NAME,
        max_tokens=MAX_SUMMARY_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def rank_articles(
    summaries: List[Dict], top_n: int = 10
) -> List[Dict]:
    """Rank summarized articles by relevance to an AI engineer."""
    summary_texts = "\n\n".join(
        f"Article {i+1}: {s['title']}\nSummary: {s['summary']}"
        for i, s in enumerate(summaries)
    )
    prompt = f"""You are an AI news ranking system. Below are summaries of today's AI news.
Rank them by relevance to a working AI engineer (not a researcher). Consider:
- Practical applicability (can they use it today?)
- Industry impact (does it change how AI is built?)
- Novelty (is this genuinely new or just incremental?)
- Actionability (does it require them to change anything?)

Return your ranking as a JSON list of article numbers in order, most relevant first.
Example: {{"ranked": [3, 1, 5, 2, 4]}}

Summaries:
{summary_texts}
"""
    response = anthropic_client.messages.create(
        model=MODEL_NAME,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )
    try:
        ranked = json.loads(response.content[0].text)
        ranked_indices = ranked["ranked"]
    except (json.JSONDecodeError, KeyError):
        print("Warning: Could not parse ranking, using original order")
        ranked_indices = list(range(1, len(summaries) + 1))

    ranked_articles = []
    for idx in ranked_indices:
        if 1 <= idx <= len(summaries):
            ranked_articles.append(summaries[idx - 1])
    return ranked_articles[:top_n]


def summarize_all_safe(articles: List[Dict]) -> List[Dict]:
    """Summarize with iteration and token spend guards."""
    summaries = []
    total_tokens_used = 0
    for i, article in enumerate(articles):
        if i >= MAX_ITERATIONS:
            print(f"  Reached max iterations ({MAX_ITERATIONS}), stopping summarization")
            break
        summary = summarize_article(article)
        token_estimate = len(summary.split()) * 1.5  # rough token estimate
        total_tokens_used += token_estimate
        if total_tokens_used > MAX_TOKENS_PER_RUN:
            print(f"  Reached max tokens per run ({MAX_TOKENS_PER_RUN}), stopping")
            break
        summaries.append({
            "title": article["title"],
            "url": article["url"],
            "summary": summary,
            "source": article["source"],
        })
        print(f"  Summarized {i+1}/{len(articles)}: {article['title'][:50]}...")
    return summaries


def write_digest(summaries: List[Dict], output_path: Path):
    """Write ranked summaries to a markdown digest file."""
    date_str = datetime.now().strftime("%A, %B %d, %Y")
    lines = [
        f"# AI News Digest — {date_str}",
        "",
        f"_{len(summaries)} curated articles from your AI feeds._",
        "",
        "---",
        "",
    ]
    for i, article in enumerate(summaries, 1):
        lines.extend([
            f"## {i}. {article['title']}",
            "",
            f"[{article['url']}]({article['url']})",
            "",
            article["summary"],
            "",
            "---",
            "",
        ])
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Digest written to {output_path}")


if __name__ == "__main__":
    print("=" * 50)
    print("  AI News Digest Generator")
    print("=" * 50)

    # Step 1: Fetch
    print("\n[1/4] Fetching RSS feeds...")
    all_articles = fetch_feeds(RSS_FEEDS)
    print(f"  Total articles fetched: {len(all_articles)}")

    # Step 2: Deduplicate
    print("\n[2/4] Deduplicating...")
    unique_articles = deduplicate(all_articles)
    print(f"  Unique articles: {len(unique_articles)} (removed {len(all_articles) - len(unique_articles)})")

    # Step 3: Summarize
    print("\n[3/4] Summarizing articles with Claude Haiku...")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("  ERROR: ANTHROPIC_API_KEY not set. Create a .env file with your key.")
        exit(1)
    summarized = summarize_all_safe(unique_articles)
    print(f"  Summarized {len(summarized)} articles")

    # Step 4: Rank and write
    print("\n[4/4] Ranking and writing digest...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ranked = rank_articles(summarized, top_n=10)
    digest_path = OUTPUT_DIR / "digest.md"
    write_digest(ranked, digest_path)

    print("\n" + "=" * 50)
    print("  Done! Open your digest:")
    print(f"  {digest_path}")
    print("=" * 50)
