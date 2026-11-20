# app/audit.py
import json, logging, sys
from datetime import datetime

logger = logging.getLogger("mcp.audit")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
logger.addHandler(handler)


def audit_log(user: str, tool: str, inputs: dict, success: bool, duration_ms: int):
    logger.info(json.dumps({
        "event": "tool_call",
        "user": user,
        "tool": tool,
        "success": success,
        "duration_ms": duration_ms,
        "timestamp": datetime.utcnow().isoformat()
    }))
