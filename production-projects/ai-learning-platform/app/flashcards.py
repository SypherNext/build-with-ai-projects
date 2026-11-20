# app/flashcards.py
import json

from anthropic import Anthropic

from app.config import settings

client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def generate_flashcards(lesson_content: str, count: int = 10) -> list[dict]:
    response = client.messages.create(
        model=settings.LLM_MODEL,
        max_tokens=2000,
        system="Generate flashcards from lesson content. Return JSON array: [{\"front\": \"question\", \"back\": \"answer\"}]",
        messages=[{"role": "user", "content": f"Lesson content:\n{lesson_content[:3000]}\n\nGenerate {count} flashcards."}]
    )
    try:
        return json.loads(response.content[0].text)
    except json.JSONDecodeError:
        return [{"front": "Error", "back": "Failed to generate flashcards"}]
