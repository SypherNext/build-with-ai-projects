# app/config.py
"""Settings loaded once from the environment."""
import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    ANTHROPIC_API_KEY: str = os.environ["ANTHROPIC_API_KEY"]
    LLM_MODEL: str = os.environ.get("LLM_MODEL", "claude-haiku-5-5")


settings = Settings()
