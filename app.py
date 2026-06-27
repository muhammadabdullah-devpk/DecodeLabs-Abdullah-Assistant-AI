"""
app.py — Main Application Entry Point
======================================
Loads Flask, registers SQLite SQLAlchemy engines, enables blueprints,
and configures Flask-Login session states.
"""

import os
from flask import Flask, redirect, url_for
from flask_login import LoginManager

from config import Config
from src.user.database import db, init_db
from src.user.models import User

# Initialize Flask Application
app = Flask(__name__)
app.config.from_object(Config)

# Ensure instance folder exists for database
os.makedirs(app.instance_path, exist_ok=True)

# Link Database connection
init_db(app)

# Setup Session Manager (Flask-Login)
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    """Retrieve active user state by primary key ID."""
    return db.session.get(User, int(user_id))

# Import blueprinted router configurations
from src.routes.main import main_bp
from src.routes.auth import auth_bp
from src.routes.chat import chat_bp
from src.routes.api import api_bp

# Mount routers
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(api_bp)

# Global error handler for unauthenticated redirects
@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for("auth.login"))

# Auto-create tables at launch inside active context
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    # Host on standard localhost development port
    app.run(host="127.0.0.1", port=5000, debug=True)
