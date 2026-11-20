# app/quiz.py
import json

from app.database import get_conn


def get_quiz(lesson_id: str, user_id: str) -> dict:
    conn = get_conn()
    quizzes = conn.execute(
        "SELECT * FROM quizzes WHERE lesson_id = ? ORDER BY RANDOM() LIMIT 3",
        (lesson_id,)
    ).fetchall()

    progress = conn.execute(
        "SELECT score FROM progress WHERE user_id = ? AND lesson_id = ?",
        (user_id, lesson_id)
    ).fetchone()
    conn.close()

    difficulty = "easy"
    if progress and progress["score"] > 0.8:
        difficulty = "hard"
    elif progress and progress["score"] > 0.5:
        difficulty = "medium"

    filtered = [q for q in quizzes if q["difficulty"] == difficulty] or quizzes

    return {
        "quizzes": [{
            "id": q["id"],
            "question": q["question"],
            "options": json.loads(q["options"]),
            "difficulty": q["difficulty"]
        } for q in filtered[:3]]
    }


def evaluate_answer(user_id: str, lesson_id: str, quiz_id: str, answer: str) -> dict:
    conn = get_conn()
    quiz = conn.execute("SELECT * FROM quizzes WHERE id = ?", (quiz_id,)).fetchone()

    is_correct = answer.strip().upper() == quiz["correct_answer"].strip().upper()

    # Update progress
    existing = conn.execute(
        "SELECT * FROM progress WHERE user_id = ? AND lesson_id = ?",
        (user_id, lesson_id)
    ).fetchone()

    if existing:
        new_attempts = existing["attempts"] + 1
        new_score = (existing["score"] * existing["attempts"] + (1.0 if is_correct else 0.0)) / new_attempts
        conn.execute(
            "UPDATE progress SET score = ?, attempts = ?, completed = ? WHERE user_id = ? AND lesson_id = ?",
            (new_score, new_attempts, 1 if new_score > 0.6 else 0, user_id, lesson_id)
        )
    else:
        conn.execute(
            "INSERT INTO progress VALUES (?, ?, ?, ?, ?)",
            (user_id, lesson_id, 1 if is_correct else 0, 1.0 if is_correct else 0.0, 1)
        )

    conn.commit()
    conn.close()

    return {
        "correct": is_correct,
        "correct_answer": quiz["correct_answer"],
        "passed": is_correct
    }
