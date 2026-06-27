"""
src/routes/chat.py — Chat and Dashboard Controllers
===================================================
Manages renders for chat workspaces, dashboards, profile and settings pages.
Implements Server-Sent Events (SSE) stream handlers for real-time text delivery.
"""

from flask import Blueprint, Response, render_template, request, redirect, url_for, current_app, session
from flask_login import login_required, current_user
import re
from src.user.models import Conversation, Setting, Usage
from src.chat.chat_service import ChatService

chat_bp = Blueprint("chat_bp", __name__)
chat_service = ChatService()

def update_session_memory(user_message: str):
    """Stores user name, recent conversation, previous topic, and greeting state in Flask sessions."""
    if "user_name" not in session:
        session["user_name"] = current_user.username
    if "greeting_history" not in session:
        session["greeting_history"] = []
    if "recent_conversation" not in session:
        session["recent_conversation"] = []
    if "previous_topic" not in session:
        session["previous_topic"] = "General Discussion"

    # Append to recent messages
    session["recent_conversation"].append(user_message)
    if len(session["recent_conversation"]) > 5:
        session["recent_conversation"].pop(0)

    # Name capture regexes
    name_patterns = [
        r"my name is ([a-zA-Z ]+)",
        r"i am ([a-zA-Z ]+)",
        r"i'?m ([a-zA-Z ]+)",
        r"call me ([a-zA-Z ]+)"
    ]
    for pattern in name_patterns:
        match = re.search(pattern, user_message, re.IGNORECASE)
        if match:
            extracted_name = match.group(1).strip().title()
            session["user_name"] = extracted_name
            break

    # Topic detection
    topics = {
        "programming": ["code", "python", "javascript", "flask", "c++", "programming", "bug", "compile"],
        "math": ["solve", "math", "calculate", "multiply", "add", "divide", "equation"],
        "ai": ["ai", "machine learning", "deep learning", "nlp", "neural network", "chatgpt", "gemini"],
        "resume": ["resume", "cv", "portfolio", "job", "career"],
    }
    for topic_name, keywords in topics.items():
        if any(kw in user_message.lower() for kw in keywords):
            session["previous_topic"] = topic_name.title()
            break

    session.modified = True


@chat_bp.route("/dashboard")
@login_required
def dashboard():
    """Render user dashboard landing showing basic usage stats and general state."""
    usage = Usage.query.filter_by(user_id=current_user.id).first()
    if not usage:
        from src.user.database import db
        usage = Usage(user_id=current_user.id)
        db.session.add(usage)
        db.session.commit()

    return render_template(
        "dashboard.html", 
        usage=usage,
        active_page="dashboard"
    )


@chat_bp.route("/chat")
@login_required
def chat_view():
    """Render main chat interface. Redirect to default or load layout directly."""
    # Find most recent conversation to auto-load, if any exists
    conversations = chat_service.get_user_conversations(current_user.id)
    active_conv_id = conversations[0].id if conversations else None
    
    settings = Setting.query.filter_by(user_id=current_user.id).first()
    theme = settings.theme if settings else "dark"

    return render_template(
        "chat.html", 
        conversations=conversations, 
        active_conv_id=active_conv_id,
        theme=theme,
        active_page="chat"
    )


@chat_bp.route("/chat/<conv_id>")
@login_required
def chat_with_id(conv_id):
    """Render main chat interface pointing directly to a specific active conversation."""
    Conversation.query.filter_by(id=conv_id, user_id=current_user.id).first_or_404()
    
    conversations = chat_service.get_user_conversations(current_user.id)
    settings = Setting.query.filter_by(user_id=current_user.id).first()
    theme = settings.theme if settings else "dark"

    return render_template(
        "chat.html", 
        conversations=conversations, 
        active_conv_id=conv_id,
        theme=theme,
        active_page="chat"
    )


@chat_bp.route("/profile")
@login_required
def profile():
    """Render user profile update panel."""
    return render_template("profile.html", active_page="profile")


@chat_bp.route("/settings")
@login_required
def settings_view():
    """Render system configurator panel."""
    settings = Setting.query.filter_by(user_id=current_user.id).first()
    if not settings:
        from src.user.database import db
        settings = Setting(user_id=current_user.id)
        db.session.add(settings)
        db.session.commit()

    return render_template("settings.html", settings=settings, active_page="settings")


@chat_bp.route("/chat/stream/<conv_id>")
@login_required
def chat_stream(conv_id):
    """EventStream endpoint generating Server-Sent Events for AI typing streaming response."""
    # Authenticate ownership
    Conversation.query.filter_by(id=conv_id, user_id=current_user.id).first_or_404()

    user_id = current_user.id
    message_content = request.args.get("message", "").strip()
    if not message_content:
        return Response("Missing message parameters", status=400)

    # Update conversation memory in session
    update_session_memory(message_content)

    # Capture session variables while request context is fully active
    session_username = session.get("user_name")
    session_topic = session.get("previous_topic")

    # Capture Flask app instance BEFORE entering the generator
    # (the generator runs in a separate thread with no request context)
    flask_app = current_app._get_current_object()

    def generate_events():
        # Push a fresh application context for the generator thread
        with flask_app.app_context():
            try:
                for chunk in chat_service.stream_response(
                    conv_id, 
                    message_content, 
                    user_id,
                    session_username=session_username,
                    session_topic=session_topic
                ):
                    # Escape carriage returns and newlines inside chunks so SSE framing isn't broken
                    safe_chunk = chunk.replace("\r\n", "\\n").replace("\n", "\\n").replace("\r", "\\n")
                    yield f"data: {safe_chunk}\n\n"
            except Exception as e:
                flask_app.logger.error(f"Stream error: {e}")
                yield "data: ⚠️ An error occurred. Please try again.\n\n"

    return Response(
        generate_events(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Transfer-Encoding": "chunked",
            "X-Accel-Buffering": "no"
        }
    )
