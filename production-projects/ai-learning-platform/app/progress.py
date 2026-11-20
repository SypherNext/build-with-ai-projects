# app/progress.py
from app.database import get_conn


def get_course_progress(user_id: str, course_id: str) -> dict:
    conn = get_conn()
    total = conn.execute(
        "SELECT COUNT(*) as c FROM lessons WHERE course_id = ?", (course_id,)
    ).fetchone()["c"]
    completed = conn.execute(
        """SELECT COUNT(*) as c FROM progress p
           JOIN lessons l ON p.lesson_id = l.id
           WHERE p.user_id = ? AND l.course_id = ? AND p.completed = 1""",
        (user_id, course_id)
    ).fetchone()["c"]
    conn.close()
    return {"total": total, "completed": completed, "percent": round(completed / total * 100) if total > 0 else 0}


def recommend_review(user_id: str) -> list:
    conn = get_conn()
    weak = conn.execute(
        """SELECT l.title, p.score FROM progress p
           JOIN lessons l ON p.lesson_id = l.id
           WHERE p.user_id = ? AND p.score < 0.6
           ORDER BY p.score ASC LIMIT 5""",
        (user_id,)
    ).fetchall()
    conn.close()
    return [{"lesson": r["title"], "score": r["score"]} for r in weak]
