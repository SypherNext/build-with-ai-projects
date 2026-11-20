# app/api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.database import get_conn, init_db
from app.flashcards import generate_flashcards
from app.generator import generate_course
from app.progress import get_course_progress, recommend_review
from app.quiz import evaluate_answer, get_quiz
from app.ratelimit import check_rate_limit

app = FastAPI(title="LearnAI API")


class GenerateRequest(BaseModel):
    topic: str
    difficulty: str = "beginner"
    user_id: str = "default"


class QuizAnswer(BaseModel):
    user_id: str
    lesson_id: str
    quiz_id: str
    answer: str


@app.on_event("startup")
async def startup():
    init_db()


@app.post("/api/courses/generate")
def create_course(req: GenerateRequest):
    if not check_rate_limit(req.user_id):
        raise HTTPException(429, "Rate limit exceeded. Try again in a minute.")
    result = generate_course(req.topic, req.difficulty)
    return result


@app.get("/api/courses")
def list_courses():
    conn = get_conn()
    courses = conn.execute("SELECT id, title, topic, lesson_count, created_at FROM courses ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(c) for c in courses]


@app.get("/api/courses/{course_id}")
def get_course(course_id: str):
    conn = get_conn()
    course = conn.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()
    if not course:
        raise HTTPException(404, "Course not found")
    lessons = conn.execute("SELECT id, title, order_index FROM lessons WHERE course_id = ? ORDER BY order_index", (course_id,)).fetchall()
    conn.close()
    return {**dict(course), "lessons": [dict(l) for l in lessons]}


@app.get("/api/lessons/{lesson_id}")
def get_lesson(lesson_id: str):
    conn = get_conn()
    lesson = conn.execute("SELECT * FROM lessons WHERE id = ?", (lesson_id,)).fetchone()
    conn.close()
    if not lesson:
        raise HTTPException(404, "Lesson not found")
    return dict(lesson)


@app.get("/api/quiz/{lesson_id}")
def quiz(lesson_id: str, user_id: str = "default"):
    return get_quiz(lesson_id, user_id)


@app.post("/api/quiz/answer")
def answer(data: QuizAnswer):
    return evaluate_answer(data.user_id, data.lesson_id, data.quiz_id, data.answer)


@app.get("/api/progress/{user_id}/{course_id}")
def progress(user_id: str, course_id: str):
    return get_course_progress(user_id, course_id)


@app.get("/api/recommendations/{user_id}")
def recommendations(user_id: str):
    return recommend_review(user_id)


@app.post("/api/flashcards/{lesson_id}")
def flashcards(lesson_id: str):
    conn = get_conn()
    lesson = conn.execute("SELECT content FROM lessons WHERE id = ?", (lesson_id,)).fetchone()
    conn.close()
    if not lesson:
        raise HTTPException(404, "Lesson not found")
    return {"flashcards": generate_flashcards(lesson["content"])}
