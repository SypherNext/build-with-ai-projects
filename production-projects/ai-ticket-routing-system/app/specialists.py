# app/specialists.py
from anthropic import Anthropic
from app.config import settings
from app.prompts import BILLING_SPECIALIST, TECHNICAL_SPECIALIST, ACCOUNT_SPECIALIST, PRODUCT_SPECIALIST

client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

SPECIALIST_PROMPTS = {
    "billing": BILLING_SPECIALIST,
    "technical": TECHNICAL_SPECIALIST,
    "account": ACCOUNT_SPECIALIST,
    "product": PRODUCT_SPECIALIST,
}


def call_specialist(specialist_type: str, subject: str, description: str) -> dict:
    system_prompt = SPECIALIST_PROMPTS.get(specialist_type, "You are a helpful support agent.")

    response = client.messages.create(
        model=settings.LLM_MODEL,
        max_tokens=1000,
        system=system_prompt,
        messages=[{
            "role": "user",
            "content": f"Ticket: {subject}\n\n{description}\n\nPlease handle this ticket:"
        }],
    )

    return {
        "specialist": specialist_type,
        "response": response.content[0].text,
        "confidence": 0.9,
        "resolution": response.content[0].text,
    }
