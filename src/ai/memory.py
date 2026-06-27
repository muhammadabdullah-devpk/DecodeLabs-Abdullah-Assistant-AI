"""
src/ai/memory.py — Conversation Context Memory
==============================================
Manages retrieval and formatting of rolling message history for the AI engines.
Ensures context fits within AI model context length limits.
"""

from typing import List, Dict
from src.user.models import Message

class ConversationMemory:
    """Manages context retrieval and formatting for chat endpoints."""

    def __init__(self, max_context_messages: int = 15) -> None:
        self.max_context_messages = max_context_messages

    def load_context(self, db_messages: List[Message], system_prompt: str) -> List[Dict[str, str]]:
        """
        Convert database messages to API-compatible prompt payloads.
        Prepends the system prompt and takes the last N messages.
        """
        payload = [{"role": "system", "content": system_prompt}]
        
        # Take only the last N messages to respect context window and rate limits
        recent_messages = db_messages[-self.max_context_messages:] if db_messages else []
        
        for msg in recent_messages:
            payload.append({
                "role": msg.role,
                "content": msg.content
            })
            
        return payload
