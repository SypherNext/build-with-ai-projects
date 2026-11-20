# app/config.py
#
# Not shown as its own code block in the lesson, but required by every other
# module: app/server.py calls `load_config()` directly, while
# app/rate_limit.py does `from app.config import config` (the already-loaded
# dict, not the loader function). Both names are exposed here so both import
# styles the lesson uses actually work.
import os

import yaml

DEFAULT_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml"
)
CONFIG_PATH = os.environ.get("MCP_CONFIG_PATH", DEFAULT_CONFIG_PATH)


def load_config(path: str = CONFIG_PATH) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


# Loaded once at import time so every module that does
# `from app.config import config` shares the same dict that
# app.server's own `config = load_config()` produces.
config = load_config()
