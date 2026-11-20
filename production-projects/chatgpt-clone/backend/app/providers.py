"""LLM provider abstraction -- from the Build lesson's Step 4.

Model ids updated to current Claude generations (the lesson's own code
used dated snapshot ids -- see the course-files fix applied alongside this
reference implementation).
"""
import os

from anthropic import Anthropic
from openai import OpenAI


class ClaudeProvider:
    def __init__(self, model="claude-haiku-5-5"):
        self.client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self.model = model

    async def stream(self, system_prompt: str, messages: list[dict]):
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system_prompt,
            messages=messages,
            stream=True,
        )
        for event in response:
            if event.type == "content_block_delta":
                yield event.delta.text


class OpenAIProvider:
    def __init__(self, model="gpt-4o-mini"):
        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.model = model

    async def stream(self, system_prompt: str, messages: list[dict]):
        formatted = [{"role": "system", "content": system_prompt}] + messages
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=formatted,
            stream=True,
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class OllamaProvider:
    def __init__(self, model="llama3.2"):
        from openai import OpenAI as OpenAILike
        self.client = OpenAILike(base_url="http://localhost:11434/v1", api_key="ollama")
        self.model = model

    async def stream(self, system_prompt: str, messages: list[dict]):
        formatted = [{"role": "system", "content": system_prompt}] + messages
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=formatted,
            stream=True,
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


PROVIDERS = {
    "claude-haiku-5-5": lambda: ClaudeProvider("claude-haiku-5-5"),
    "claude-sonnet-5-5": lambda: ClaudeProvider("claude-sonnet-5-5"),
    "gpt-4o-mini": lambda: OpenAIProvider("gpt-4o-mini"),
    "ollama": lambda: OllamaProvider(),
}


def get_provider(model_id: str):
    factory = PROVIDERS.get(model_id)
    if not factory:
        raise ValueError(f"Unknown model: {model_id}")
    return factory()
