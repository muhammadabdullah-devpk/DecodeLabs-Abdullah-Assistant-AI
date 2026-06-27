"""
src/routes/api.py — REST API Endpoints
=======================================
API endpoints for AJAX UI interactions:
- Fetch, rename, pin, folder-categorize, and delete conversations.
- Retrieve real-time token usage stats and charts.
- Save customizable settings (themes, model selects, prompts, custom keys).
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from src.user.database import db
from src.user.models import Conversation, Message, Setting, Usage
from src.chat.chat_service import ChatService
from src.chat.history import format_chat_timestamp

api_bp = Blueprint("api", __name__, url_prefix="/api")
chat_service = ChatService()

@api_bp.route("/conversations", methods=["GET", "POST"])
@login_required
def conversations():
    """GET list of conversations or POST a new conversation."""
    if request.method == "POST":
        data = request.get_json() or {}
        title = data.get("title", "New Chat").strip()
        folder = data.get("folder_name", "General").strip()
        
        conv = chat_service.create_conversation(
            user_id=current_user.id,
            title=title if title else "New Chat",
            folder_name=folder if folder else "General"
        )
        return jsonify({
            "id": conv.id,
            "title": conv.title,
            "folder_name": conv.folder_name,
            "is_pinned": conv.is_pinned,
            "created_at": conv.created_at.isoformat()
        }), 201
        
    conversations_list = chat_service.get_user_conversations(current_user.id)
    return jsonify([{
        "id": c.id,
        "title": c.title,
        "folder_name": c.folder_name,
        "is_pinned": c.is_pinned,
        "updated_at": format_chat_timestamp(c.updated_at)
    } for c in conversations_list])


@api_bp.route("/conversations/<conv_id>", methods=["GET", "PUT", "DELETE"])
@login_required
def conversation_detail(conv_id):
    """GET conversation messages, PUT update title/folder, DELETE conversation."""
    conv = Conversation.query.filter_by(id=conv_id, user_id=current_user.id).first_or_404()

    if request.method == "GET":
        messages = chat_service.get_conversation_messages(conv_id)
        return jsonify({
            "id": conv.id,
            "title": conv.title,
            "folder_name": conv.folder_name,
            "messages": [{
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "timestamp": format_chat_timestamp(m.timestamp),
                "rating": m.rating
            } for m in messages]
        })

    elif request.method == "PUT":
        data = request.get_json() or {}
        title = data.get("title", "").strip()
        folder = data.get("folder_name", "").strip()

        if title:
            conv.title = title
        if folder:
            conv.folder_name = folder

        db.session.commit()
        return jsonify({"message": "Conversation updated successfully."})

    elif request.method == "DELETE":
        db.session.delete(conv)
        db.session.commit()
        return jsonify({"message": "Conversation deleted successfully."})


@api_bp.route("/conversations/<conv_id>/pin", methods=["POST"])
@login_required
def pin_conversation(conv_id):
    """Toggle the pin status of a conversation."""
    conv = Conversation.query.filter_by(id=conv_id, user_id=current_user.id).first_or_404()
    conv.is_pinned = not conv.is_pinned
    db.session.commit()
    return jsonify({
        "id": conv.id,
        "is_pinned": conv.is_pinned,
        "message": f"Conversation {'pinned' if conv.is_pinned else 'unpinned'} successfully."
    })


@api_bp.route("/conversations/<conv_id>/message/<int:msg_id>/rate", methods=["POST"])
@login_required
def rate_message(conv_id, msg_id):
    """Rate a message (1: like, -1: dislike, 0: reset)."""
    # Ensure message belongs to a conversation owned by the current user
    msg = Message.query.join(Conversation).filter(
        Message.id == msg_id,
        Conversation.id == conv_id,
        Conversation.user_id == current_user.id
    ).first_or_404()
    
    data = request.get_json() or {}
    rating = data.get("rating", 0)
    if rating not in [1, -1, 0]:
        return jsonify({"error": "Invalid rating value."}), 400
        
    msg.rating = rating
    db.session.commit()
    return jsonify({"message": "Message rated successfully.", "rating": msg.rating})


@api_bp.route("/settings", methods=["POST"])
@login_required
def update_settings():
    """Update settings (theme, API key, model selection, prompt overrides)."""
    data = request.get_json() or {}
    
    settings = Setting.query.filter_by(user_id=current_user.id).first()
    if not settings:
        settings = Setting(user_id=current_user.id)
        db.session.add(settings)
        
    theme = data.get("theme", "").strip()
    gemini_key = data.get("gemini_key", "").strip()
    ai_model = data.get("ai_model", "").strip()
    system_prompt = data.get("system_prompt", "").strip()

    if theme in ["dark", "light"]:
        settings.theme = theme
    if gemini_key is not None:
        settings.gemini_key = gemini_key
    if ai_model:
        settings.ai_model = ai_model
    if system_prompt:
        settings.system_prompt = system_prompt

    db.session.commit()
    return jsonify({"message": "Settings updated successfully."})


@api_bp.route("/usage", methods=["GET"])
@login_required
def get_usage():
    """Retrieve usage stats metrics for SaaS dashboards."""
    usage = Usage.query.filter_by(user_id=current_user.id).first()
    if not usage:
        usage = Usage(user_id=current_user.id)
        db.session.add(usage)
        db.session.commit()

    return jsonify({
        "tokens_total": usage.tokens_total,
        "messages_count": usage.messages_count,
        "last_active": usage.last_active.isoformat() if usage.last_active else None
    })
