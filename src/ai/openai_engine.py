"""
src/ai/openai_engine.py — OpenAI API Service Connection
======================================================
Manages direct client connections to OpenAI's API.
Supports streaming responses chunk-by-chunk using modern client syntax.
"""

from typing import Generator, List, Dict
import openai
import config

class OpenAIEngine:
    """Handles API requests and response streams with OpenAI."""

    def __init__(self, api_key: str = "") -> None:
        # Fall back to global config key if no session/custom key is provided
        self.api_key = api_key if api_key else config.Config.OPENAI_API_KEY

    def is_available(self) -> bool:
        """Check if an API key is configured."""
        return bool(self.api_key.strip())

    def get_client(self) -> openai.OpenAI:
        """Return a configured OpenAI client instance."""
        return openai.OpenAI(api_key=self.api_key)

    def generate_stream(self, messages: List[Dict[str, str]], model: str = "gpt-4o") -> Generator[str, None, None]:
        """
        Query OpenAI ChatCompletion endpoint and yield chunks in real-time.
        Raises exceptions on network errors, invalid keys, or limits.
        """
        if not self.is_available():
            raise ValueError("No OpenAI API key is configured.")

        client = self.get_client()
        
        # Call the chat completion endpoint with streaming active
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True
        )

        for chunk in response:
            if chunk.choices and len(chunk.choices) > 0:
                content = chunk.choices[0].delta.content
                if content is not None:
                    yield content
