"""AI Resume Reviewer -- analyses a resume against a job description and scores the match."""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    print("Error: ANTHROPIC_API_KEY not set in .env")
    sys.exit(1)

import anthropic
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def load_text(source: str) -> str:
    """Load text from a file or return the input as-is."""
    path = Path(source)
    if path.exists():
        return path.read_text(encoding="utf-8")
    return source


ANALYSIS_DIMENSIONS = [
    {
        "name": "skills_match",
        "label": "Skills Match",
        "description": "How well do the candidate's technical and soft skills match the requirements?"
    },
    {
        "name": "experience_relevance",
        "label": "Experience Relevance",
        "description": "How relevant is the candidate's work experience to the role?"
    },
    {
        "name": "achievements_impact",
        "label": "Achievements & Impact",
        "description": "Does the resume show measurable impact and concrete achievements?"
    },
    {
        "name": "keyword_optimization",
        "label": "Keyword Optimization",
        "description": "How well does the resume include keywords from the job description?"
    },
    {
        "name": "format_clarity",
        "label": "Format & Clarity",
        "description": "Is the resume well-structured, concise, and easy to scan?"
    },
]

SYSTEM_PROMPT = """You are an expert resume reviewer and career coach. Analyse the resume against the job description and provide a structured evaluation.

For each dimension, provide:
- score: 0-100
- evidence: specific quotes or examples from the resume
- gaps: what's missing or weak
- suggestion: how to improve

Return your analysis as a JSON object with this exact structure:
{
  "overall_score": 0-100,
  "dimensions": {
    "skills_match": {"score": 0-100, "evidence": "...", "gaps": "...", "suggestion": "..."},
    "experience_relevance": {"score": 0-100, "evidence": "...", "gaps": "...", "suggestion": "..."},
    "achievements_impact": {"score": 0-100, "evidence": "...", "gaps": "...", "suggestion": "..."},
    "keyword_optimization": {"score": 0-100, "evidence": "...", "gaps": "...", "suggestion": "..."},
    "format_clarity": {"score": 0-100, "evidence": "...", "gaps": "...", "suggestion": "..."}
  },
  "strengths": ["strength1", "strength2", "strength3"],
  "critical_gaps": ["gap1", "gap2"],
  "quick_wins": ["quick fix 1", "quick fix 2", "quick fix 3"],
  "recommended_actions": ["action1", "action2", "action3"],
  "ats_fit_score": 0-100,
  "ats_notes": "Notes on ATS keywords and formatting"
}

Be specific and actionable. A score of 70 means the resume is decent but has clear room for improvement. Scores below 50 indicate significant gaps."""


def analyze_resume(resume_text: str, job_description: str) -> dict:
    """Analyse a resume against a job description. Returns structured analysis."""
    user_message = f"""RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

Analyse this resume against the job description. Return the JSON analysis."""

    response = client.messages.create(
        model="claude-haiku-5-5",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}]
    )

    response_text = response.content[0].text
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens

    print(f"  Input tokens: {input_tokens}, Output tokens: {output_tokens}")

    # Parse JSON from response
    try:
        # Find JSON block in response
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = response_text.strip()
        return json.loads(json_str)
    except json.JSONDecodeError:
        print("Warning: Could not parse JSON, returning raw text")
        return {"raw_response": response_text}


def format_report(analysis: dict) -> str:
    """Format the analysis as a readable Markdown report."""
    if "raw_response" in analysis:
        return analysis["raw_response"]

    lines = []
    lines.append("# Resume Analysis Report\n")
    lines.append(f"## Overall Score: {analysis.get('overall_score', 'N/A')}/100")
    lines.append(f"ATS Fit Score: {analysis.get('ats_fit_score', 'N/A')}/100\n")

    lines.append("## Dimension Scores\n")
    dims = analysis.get("dimensions", {})
    for dim_key, dim_data in dims.items():
        label = dim_key.replace("_", " ").title()
        score = dim_data.get("score", "N/A")
        bar = "█" * (score // 10) + "░" * (10 - score // 10) if isinstance(score, int) else ""
        lines.append(f"### {label}: {score}/100")
        if bar:
            lines.append(f"`{bar}`")
        lines.append(f"- **Evidence:** {dim_data.get('evidence', 'N/A')}")
        lines.append(f"- **Gaps:** {dim_data.get('gaps', 'N/A')}")
        lines.append(f"- **Suggestion:** {dim_data.get('suggestion', 'N/A')}\n")

    lines.append("## Strengths\n")
    for s in analysis.get("strengths", []):
        lines.append(f"- ✅ {s}")

    lines.append("\n## Critical Gaps\n")
    for g in analysis.get("critical_gaps", []):
        lines.append(f"- ❌ {g}")

    lines.append("\n## Quick Wins\n")
    for q in analysis.get("quick_wins", []):
        lines.append(f"- ⚡ {q}")

    lines.append("\n## Recommended Actions\n")
    for a in analysis.get("recommended_actions", []):
        lines.append(f"- {a}")

    if analysis.get("ats_notes"):
        lines.append(f"\n## ATS Notes\n{analysis['ats_notes']}")

    return "\n".join(lines)


def main():
    print("=" * 50)
    print("  AI Resume Reviewer")
    print("=" * 50)

    # Get resume
    print("\n--- Resume ---")
    resume_source = input("Enter resume text or file path: ").strip()
    resume_text = load_text(resume_source)
    print(f"Resume loaded: {len(resume_text)} characters")

    # Get job description
    print("\n--- Job Description ---")
    jd_source = input("Enter job description text or file path: ").strip()
    jd_text = load_text(jd_source)
    print(f"Job description loaded: {len(jd_text)} characters")

    print("\n" + "=" * 50)
    print("Analysing...")
    print("=" * 50 + "\n")

    analysis = analyze_resume(resume_text, jd_text)

    report = format_report(analysis)
    print(report)

    # Save option
    save = input("\nSave report to file? (y/n): ").strip().lower()
    if save == "y":
        from datetime import datetime
        output_dir = Path("reports")
        output_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"resume_review_{timestamp}.md"
        output_path.write_text(report, encoding="utf-8")
        print(f"Report saved to: {output_path}")


if __name__ == "__main__":
    main()
