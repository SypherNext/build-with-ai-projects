"""Settings loaded once from the environment."""
import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    ANTHROPIC_API_KEY: str = os.environ["ANTHROPIC_API_KEY"]
    # Specialist agents are cheap, high-volume calls -- Haiku handles them.
    # The supervisor and coordinator each run at most once per ticket, so
    # they use a stronger model directly (see supervisor.py / coordinator.py).
    LLM_MODEL: str = os.environ.get("LLM_MODEL", "claude-haiku-5-5")
    PORT: int = int(os.environ.get("PORT", "8000"))


settings = Settings()
