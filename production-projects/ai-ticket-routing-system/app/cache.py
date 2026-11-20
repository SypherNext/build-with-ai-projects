# app/cache.py
from app.specialists import call_specialist

cache = {}  # Simple in-memory; replace with Redis in production


def cached_specialist(specialist_type: str, subject: str, description: str):
    key = f"{specialist_type}:{hash(subject + description)}"
    if key in cache:
        return cache[key]
    result = call_specialist(specialist_type, subject, description)
    cache[key] = result
    return result
