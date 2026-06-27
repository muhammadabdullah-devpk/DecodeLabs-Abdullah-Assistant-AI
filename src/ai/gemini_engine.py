"""
src/ai/gemini_engine.py — Google Gemini API Service (google-genai SDK)
=======================================================================
Uses the official google-genai SDK (newer, cleaner API) to connect to
Google Gemini models. Supports streaming text generation with full
conversation history context.
"""

from typing import Generator, List, Dict, Optional
import config


class GeminiEngine:
    """Handles API requests and streaming responses with Google Gemini (google-genai SDK)."""

    def __init__(self, api_key: str = "") -> None:
        # Prefer user-level key, fall back to global config key
        self.api_key = api_key.strip() if api_key and api_key.strip() else config.Config.GEMINI_API_KEY
        self._client = None

    def _get_client(self):
        """Lazy-initialize the Gemini client."""
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def is_available(self) -> bool:
        """Check if a valid API key is configured."""
        return bool(self.api_key)

    def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model_name: str = "models/gemini-2.5-flash"
    ) -> Generator[str, None, None]:
        """
        Query Gemini API and yield response text chunks in real-time.

        Converts the internal message list format:
          [{"role": "system"|"user"|"assistant", "content": "..."}]
        into Gemini's Content format.
        """
        if not self.is_available():
            raise ValueError("No Google Gemini API key is configured.")

        from google.genai import types

        # Extract system instruction from the message list
        system_instruction: Optional[str] = None
        contents: List[types.Content] = []

        for msg in messages:
            role = msg.get("role", "user")
            text = msg.get("content", "")

            if role == "system":
                system_instruction = text
                continue

            # Gemini roles: "user" or "model"
            gemini_role = "model" if role == "assistant" else "user"
            contents.append(
                types.Content(
                    role=gemini_role,
                    parts=[types.Part(text=text)]
                )
            )

        config_kwargs = {}
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction

        client = self._get_client()
        response = client.models.generate_content_stream(
            model=model_name or "models/gemini-2.5-flash",
            contents=contents,
            config=types.GenerateContentConfig(**config_kwargs) if config_kwargs else None
        )

        for chunk in response:
            if chunk.text:
                yield chunk.text
