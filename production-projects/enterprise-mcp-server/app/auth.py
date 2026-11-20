# app/auth.py
import hashlib
from typing import Optional, Dict

TOKENS = {}  # In production, load from database


def init_tokens(tokens_config: list[dict]):
    for t in tokens_config:
        key_hash = hashlib.sha256(t["token"].encode()).hexdigest()
        TOKENS[key_hash] = {
            "user": t["user"],
            "scopes": t["scopes"]
        }


def authenticate(headers: Optional[Dict]) -> Optional[Dict]:
    if not headers:
        return None
    auth_header = headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:]
    key_hash = hashlib.sha256(token.encode()).hexdigest()
    return TOKENS.get(key_hash)
