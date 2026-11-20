# app/coordinator.py
from anthropic import Anthropic
from app.config import settings
from app.state import SpecialistResponse
import json

client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def coordinate_responses(responses: list[SpecialistResponse], subject: str) -> str:
    context = "\n\n".join([
        f"[{r['specialist'].upper()}]\n{r['response']}"
        for r in responses
    ])

    response = client.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=1000,
        system="You are a support coordinator. Combine the specialist responses into a single coherent answer for the customer.",
        messages=[{
            "role": "user",
            "content": f"Subject: {subject}\n\nSpecialist responses:\n{context}\n\nCombine into one response:"
        }],
    )
    return response.content[0].text
