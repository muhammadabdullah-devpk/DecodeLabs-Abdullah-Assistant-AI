"""
src/chat/chat_service.py — Conversation Lifecycle Manager
==========================================================
Coordinates database records, conversation context generation, OpenAI connections,
and local rule engines. Saves chats and tokens consumed.
"""

from typing import Generator, List, Optional
from src.user.database import db
from src.user.models import Conversation, Message, Setting, Usage
from src.ai.memory import ConversationMemory
from src.ai.gemini_engine import GeminiEngine
from src.ai.fallback_engine import FallbackEngine
from src.ai.prompt_manager import PromptManager

class ChatService:
    """Manages chats, message storage, context gathering, and streaming orchestration."""

    def __init__(self) -> None:
        self.memory_manager = ConversationMemory()
        self.fallback_engine = FallbackEngine()

    def create_conversation(self, user_id: int, title: str = "New Chat", folder_name: str = "General") -> Conversation:
        """Create a new chat conversation database record."""
        conv = Conversation(user_id=user_id, title=title, folder_name=folder_name)
        db.session.add(conv)
        db.session.commit()
        return conv

    def get_user_conversations(self, user_id: int) -> List[Conversation]:
        """Fetch all conversation records for a given user, ordered by updated_at."""
        return Conversation.query.filter_by(user_id=user_id).order_by(Conversation.updated_at.desc()).all()

    def get_conversation_messages(self, conversation_id: str) -> List[Message]:
        """Fetch all message records in a conversation, ordered chronologically."""
        return Message.query.filter_by(conversation_id=conversation_id).order_by(Message.timestamp.asc()).all()

    def save_message(self, conversation_id: str, role: str, content: str, tokens: int = 0) -> Message:
        """Save a new message record to the database."""
        from datetime import datetime
        msg = Message(conversation_id=conversation_id, role=role, content=content, tokens_used=tokens)
        db.session.add(msg)
        
        # Touch conversation updated timestamp
        conv = Conversation.query.get(conversation_id)
        if conv:
            conv.updated_at = datetime.utcnow()
            
        db.session.commit()
        return msg

    def stream_response(
        self, 
        conversation_id: str, 
        user_message: str, 
        user_id: int,
        session_username: Optional[str] = None,
        session_topic: Optional[str] = None
    ) -> Generator[str, None, None]:
        """
        Executes the AI generation stream.
        Saves user query, runs Gemini stream, falls back to local rules if needed,
        and saves completed assistant reply to database.
        """
        # 1. Save user message to database
        self.save_message(conversation_id, "user", user_message)

        # 2. Get user preferences / custom keys
        settings = Setting.query.filter_by(user_id=user_id).first()
        if not settings:
            # Create default settings record
            settings = Setting(user_id=user_id)
            db.session.add(settings)
            db.session.commit()

        # Update usage metrics
        usage = Usage.query.filter_by(user_id=user_id).first()
        if not usage:
            usage = Usage(user_id=user_id)
            db.session.add(usage)
            db.session.commit()
            
        usage.messages_count += 1
        db.session.commit()

        # Get system prompt
        sys_prompt = PromptManager.get_prompt(custom_override=settings.system_prompt)

        # Personalize system prompt dynamically with active session facts passed from request thread
        user_name = session_username if session_username else (settings.user.username if settings.user else "User")
        prev_topic = session_topic if session_topic else "General Discussion"

        personalized_prompt = (
            f"{sys_prompt}\n\n"
            f"Active Session Memory:\n"
            f"- User Name: {user_name}\n"
            f"- Current Session Topic focus: {prev_topic}\n"
        )

        # 3. Retrieve conversation history
        messages_db = self.get_conversation_messages(conversation_id)
        
        # Load active context history with the personalized prompt
        api_payload = self.memory_manager.load_context(messages_db[:-1], personalized_prompt)

        # Append active user message to context payload
        api_payload.append({"role": "user", "content": user_message})

        # 4. Generate AI Stream
        ai_engine = GeminiEngine(api_key=settings.gemini_key)
        full_reply = ""
        is_fallback = False

        if ai_engine.is_available():
            try:
                stream = ai_engine.generate_stream(api_payload, model_name=settings.ai_model)
                for chunk in stream:
                    full_reply += chunk
                    yield chunk
            except Exception as e:
                import traceback
                print(f"[GeminiEngine Error] {e}\n{traceback.format_exc()}")
                is_fallback = True
        else:
            is_fallback = True

        if is_fallback:
            # Get user name safely from passed parameter or db (avoids DetachedInstanceError)
            user_display_name = session_username
            if not user_display_name:
                from src.user.models import User
                user_rec = db.session.get(User, user_id)
                user_display_name = user_rec.username if user_rec else "there"
            
            # Generate response from local engine
            fallback_text = self.fallback_engine.generate(user_message, username=user_display_name)
            
            # Simulate streaming chunks for UI consistency
            chunk_size = 8
            for i in range(0, len(fallback_text), chunk_size):
                chunk = fallback_text[i:i+chunk_size]
                full_reply += chunk
                yield chunk

        # 5. Save assistant reply to database
        self.save_message(conversation_id, "assistant", full_reply)
        
        # Save placeholder tokens
        approx_tokens = len(user_message.split()) + len(full_reply.split())
        usage.tokens_total += approx_tokens
        db.session.commit()
