"""
src/chat/history.py — Chat History Formatting
=============================================
Provides helper formatting functions for dates, timings, and logs.
"""

from datetime import datetime

def format_chat_timestamp(dt: datetime) -> str:
    """Format datetime into a clean user-facing timestamp."""
    if not dt:
        return ""
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days == 0:
        return dt.strftime("Today at %I:%M %p")
    elif diff.days == 1:
        return dt.strftime("Yesterday at %I:%M %p")
    elif diff.days < 7:
        return dt.strftime("%A at %I:%M %p")
    else:
        return dt.strftime("%b %d, %Y %I:%M %p")
