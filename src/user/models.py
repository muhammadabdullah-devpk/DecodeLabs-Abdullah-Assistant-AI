"""
src/user/models.py — SQLAlchemy Models
======================================
Defines schemas for Users, Conversations, Messages, Settings, and API Usage.
"""

from datetime import datetime
import uuid
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from src.user.database import db

class User(db.Model, UserMixin):
    """User account details for authentication and profiling."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    avatar_url = db.Column(db.String(256), default="/static/img/avatar-default.png")

    # Relationships
    conversations = db.relationship("Conversation", backref="user", lazy=True, cascade="all, delete-orphan")
    settings = db.relationship("Setting", backref="user", uselist=False, lazy=True, cascade="all, delete-orphan")
    usage = db.relationship("Usage", backref="user", uselist=False, lazy=True, cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        """Hash and store password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify hashed password."""
        return check_password_hash(self.password_hash, password)


class Conversation(db.Model):
    """Chat session metadata holding reference to User."""
    __tablename__ = "conversations"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(128), default="New Chat")
    folder_name = db.Column(db.String(64), default="General")
    is_pinned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    messages = db.relationship("Message", backref="conversation", lazy=True, cascade="all, delete-orphan")


class Message(db.Model):
    """Individual message exchange between user and bot."""
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.String(36), db.ForeignKey("conversations.id"), nullable=False)
    role = db.Column(db.String(16), nullable=False)  # 'user', 'assistant' or 'system'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    rating = db.Column(db.Integer, default=0)  # 0: neutral, 1: liked, -1: disliked
    tokens_used = db.Column(db.Integer, default=0)


class Setting(db.Model):
    """User-level customized configurations (e.g. key override, model)."""
    __tablename__ = "settings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    theme = db.Column(db.String(16), default="dark")  # 'dark' or 'light'
    gemini_key = db.Column(db.String(256), default="")  # optional user-level key
    ai_model = db.Column(db.String(64), default="models/gemini-2.5-flash")
    system_prompt = db.Column(
        db.Text, 
        default="You are Abdullah Assistant AI, a helpful, professional, and intelligent AI SaaS assistant. Answer clearly and comprehensively."
    )


class Usage(db.Model):
    """Usage stats logging for SaaS API token consumption."""
    __tablename__ = "usages"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    tokens_total = db.Column(db.Integer, default=0)
    messages_count = db.Column(db.Integer, default=0)
    last_active = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
