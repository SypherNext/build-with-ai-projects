# app/cache.py
"""Course-generation caching (Deploy lesson, Production Hardening #1).

The lesson's own snippet only showed the write path (`cache_course`). A
cache nobody ever reads from is pointless, so this reference implementation
adds the matching read path (`get_cached_course`) and keys on topic AND
difficulty -- the original snippet hashed on topic alone, which would wrongly
return a "beginner" course for a "beginner" lookup when the cached entry was
written for a different difficulty, or vice versa.
"""
import hashlib
import json

from app.database import get_conn


def _cache_key(topic: str, difficulty: str) -> str:
    raw = f"{topic.strip().lower()}::{difficulty.strip().lower()}"
    return f"course:{hashlib.md5(raw.encode()).hexdigest()}"


def cache_course(topic: str, difficulty: str, course_data: dict):
    key = _cache_key(topic, difficulty)
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO cache (key, value) VALUES (?, ?)",
        (key, json.dumps(course_data)),
    )
    conn.commit()
    conn.close()


def get_cached_course(topic: str, difficulty: str) -> dict | None:
    key = _cache_key(topic, difficulty)
    conn = get_conn()
    row = conn.execute("SELECT value FROM cache WHERE key = ?", (key,)).fetchone()
    conn.close()
    return json.loads(row["value"]) if row else None
