# app/validation.py
import re
from typing import Any

BLOCKED_SQL_PATTERNS = [
    r"DROP\s+TABLE", r"DROP\s+DATABASE", r"TRUNCATE", r"ALTER\s+TABLE",
    r"EXEC\s+xp_", r"INTO\s+OUTFILE", r"pg_sleep", r"BENCHMARK"
]


def validate_sql_query(query: str) -> bool:
    for pattern in BLOCKED_SQL_PATTERNS:
        if re.search(pattern, query, re.IGNORECASE):
            return False
    return True


def sanitize_input(value: Any, max_length: int = 5000) -> str:
    text = str(value)
    if len(text) > max_length:
        text = text[:max_length] + "... [truncated]"
    return text
