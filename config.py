"""
config.py — DecodeBot AI SaaS Configuration
===========================================
Central settings for Flask, SQLAlchemy database, and OpenAI models.
Values are loaded from environment variables or .env with secure defaults.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load local environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

class Config:
    """Base configuration class."""
    
    # ── Flask Configuration ───────────────────────────────────────────────────
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev_secret_key_decodebot_ai_99x77")
    
    # ── Database (SQLAlchemy) ─────────────────────────────────────────────────
    # SQLite file located in /instance/database.db
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", 
        f"sqlite:///{BASE_DIR / 'instance' / 'database.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # ── AI Engine Configuration ───────────────────────────────────────────────
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "models/gemini-2.5-flash")
    
    # ── Application Settings ──────────────────────────────────────────────────
    APP_NAME = "Abdullah Assistant AI"
    APP_VERSION = "3.0.0"
    APP_AUTHOR = "Muhammad Abdullah"
    
    # ── Session & Security ────────────────────────────────────────────────────
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 86400 * 30  # 30 days

# ── Backward-Compatible Flat Attributes ──────────────────────────────────────
# Legacy src/ modules (utils.py, response_generator.py, chatbot_engine.py) still
# import from config as flat attributes.  Keep them here so nothing breaks.
BOT_NAME            = "Abdullah Assistant AI"
BOT_VERSION         = "3.0.0"
BOT_AUTHOR          = "Muhammad Abdullah"
LOGGING_ENABLED     = False
TYPING_EFFECT_ENABLED = True
TYPING_SPEED        = 0.01
MATH_ENABLED        = True
MAX_FALLBACK_BEFORE_SUGGESTION = 3

# ── Legacy CLI / Logging Attributes ─────────────────────────────────────────
LOG_FILE   = "logs/chat.log"
LOG_FORMAT = "[{timestamp}] {speaker}: {message}"
COLORS = {
    "BOT_NAME":  "CYAN",
    "BOT_MSG":   "WHITE",
    "USER_MSG":  "GREEN",
    "SEPARATOR": "YELLOW",
    "SYSTEM":    "MAGENTA",
    "ERROR":     "RED",
    "SUCCESS":   "GREEN",
    "DATE_TIME": "BLUE",
}

# ── Legacy Color Shorthand Attributes ────────────────────────────────────────
COLOR_BOT    = "CYAN"
COLOR_USER   = "GREEN"
COLOR_SYSTEM = "MAGENTA"
COLOR_ERROR  = "RED"
COLOR_DIM    = "WHITE"

# ── Legacy Typing Animation ──────────────────────────────────────────────────
TYPING_PAUSE = 0.3

# ── Legacy Data File Paths ───────────────────────────────────────────────────
INTENTS_FILE   = "data/intents.json"
RESPONSES_FILE = "data/responses.json"

# ── Legacy Memory & Fallback Limits ─────────────────────────────────────────
MAX_HISTORY        = 50
FALLBACK_THRESHOLD = 3
