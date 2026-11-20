# app/rate_limit.py
import time
from collections import defaultdict
# The lesson's own code block uses the `Dict` annotation below without this
# import -- a real NameError at module-load time (annotations on a
# module-level assignment are evaluated eagerly). Added here so the module
# actually imports.
from typing import Dict

_limits: Dict[str, list] = defaultdict(list)


def check_rate_limit(tool_name: str, user: str) -> bool:
    from app.config import config
    tool_def = next(t for t in config["tools"] if t["name"] == tool_name)
    max_rpm = tool_def["rate_limit"]
    key = f"{user}:{tool_name}"
    now = time.time()

    _limits[key] = [t for t in _limits[key] if now - t < 60]
    if len(_limits[key]) >= max_rpm:
        return False
    _limits[key].append(now)
    return True
