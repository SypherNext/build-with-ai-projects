# app/generator.py
from datetime import datetime
import json
import uuid

from anthropic import Anthropic

from app.cache import cache_course, get_cached_course
from app.config import settings
from app.database import get_conn

client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def generate_course(topic: str, difficulty: str = "beginner") -> dict:
    course_data = get_cached_course(topic, difficulty)

    if course_data is None:
        prompt = f"""Generate a structured course outline for "{topic}" at {difficulty} level.

Return JSON:
{{
    "title": "Course title",
    "description": "2-3 sentence description",
    "lessons": [
        {{
            "title": "Lesson title",
            "content": "Full lesson content (500-1000 words with examples)",
            "order_index": 1,
            "quizzes": [
                {{
                    "question": "Quiz question",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": "A",
                    "difficulty": "easy|medium|hard"
                }}
            ]
        }}
    ]
}}

Generate 5-8 lessons with 2-3 quizzes per lesson."""

        response = client.messages.create(
            model=settings.LLM_MODEL,
            max_tokens=8000,
            system=f"You are an expert educator creating a {difficulty}-level course. Be thorough and accurate.",
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            course_data = json.loads(response.content[0].text)
        except json.JSONDecodeError:
            raise ValueError("Failed to parse course generation output")

        cache_course(topic, difficulty, course_data)

    # Save to database
    conn = get_conn()
    course_id = uuid.uuid4().hex[:12]
    conn.execute(
        "INSERT INTO courses VALUES (?, ?, ?, ?, ?, ?)",
        (course_id, course_data["title"], topic, course_data["description"],
         len(course_data["lessons"]), datetime.utcnow().isoformat())
    )

    for lesson in course_data["lessons"]:
        lesson_id = uuid.uuid4().hex[:12]
        conn.execute(
            "INSERT INTO lessons VALUES (?, ?, ?, ?, ?)",
            (lesson_id, course_id, lesson["title"], lesson["content"], lesson["order_index"])
        )
        for quiz in lesson.get("quizzes", []):
            conn.execute(
                "INSERT INTO quizzes (id, lesson_id, question, options, correct_answer, difficulty) VALUES (?, ?, ?, ?, ?, ?)",
                (uuid.uuid4().hex[:12], lesson_id, quiz["question"],
                 json.dumps(quiz["options"]), quiz["correct_answer"], quiz.get("difficulty", "medium"))
            )

    conn.commit()
    conn.close()
    return {"course_id": course_id, "title": course_data["title"], "lessons": len(course_data["lessons"])}
