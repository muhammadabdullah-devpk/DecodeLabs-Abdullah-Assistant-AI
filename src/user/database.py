"""
src/user/database.py — Database Instance Loader
================================================
Initializes the SQLAlchemy object to be shared across blueprints and route modules.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app) -> None:
    """Initialize database connection with Flask app context."""
    db.init_app(app)
