# app/supervisor.py
from anthropic import Anthropic
from app.config import settings
import json

client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def supervisor_route(subject: str, description: str) -> dict:
    prompt = f"""Analyze this support ticket and determine which specialist should handle it.

Subject: {subject}
Description: {description}

Choose the best routing:
- "billing": Payment, invoice, refund, subscription issues
- "technical": Bugs, errors, API, configuration, performance
- "account": Access, permissions, SSO, team management
- "product": Feature requests, roadmap, feedback
- "multi": Requires multiple specialists (rare)

Return JSON: {{"decision": "billing|technical|account|product|multi", "reasoning": "brief explanation", "confidence": 0.0-1.0}}"""

    response = client.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )

    return json.loads(response.content[0].text)
