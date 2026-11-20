# app/ratelimit.py
"""Per-user rate limiting (Deploy lesson, Production Hardening #2).

In-memory and per-process -- fine for this single-container reference, but
note in a multi-worker/multi-instance deployment each process would track
its own counts (see README/Deploy lesson notes).
"""
from collections import defaultdict
import time

user_requests = defaultdict(list)


def check_rate_limit(user_id: str, max_per_minute: int = 10) -> bool:
    now = time.time()
    user_requests[user_id] = [t for t in user_requests[user_id] if now - t < 60]
    if len(user_requests[user_id]) >= max_per_minute:
        return False
    user_requests[user_id].append(now)
    return True
