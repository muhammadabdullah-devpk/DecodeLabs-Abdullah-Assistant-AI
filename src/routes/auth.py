"""
src/routes/auth.py — Authentication Route Handlers
==================================================
Manages register, login, logout, and profile configuration endpoints.
Defines user-session wrappers using Flask-Login and secure hashing.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from src.user.database import db
from src.user.models import User, Setting, Usage

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Sign up a new user account."""
    if current_user.is_authenticated:
        return redirect(url_for("chat_bp.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for("auth.register"))

        # Check existing username/email
        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
            return redirect(url_for("auth.register"))
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return redirect(url_for("auth.register"))

        # Create new user
        new_user = User(username=username, email=email)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        # Seed default settings and usage records
        user_settings = Setting(user_id=new_user.id)
        user_usage = Usage(user_id=new_user.id)
        db.session.add(user_settings)
        db.session.add(user_usage)
        db.session.commit()

        login_user(new_user)
        flash("Registration successful! Welcome to Abdullah Assistant AI.", "success")
        return redirect(url_for("chat_bp.dashboard"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Login to an existing account."""
    if current_user.is_authenticated:
        return redirect(url_for("chat_bp.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        remember = True if request.form.get("remember") else False

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("auth.login"))

        login_user(user, remember=remember)
        return redirect(url_for("chat_bp.dashboard"))

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    """Sign out the current user session."""
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))


@auth_bp.route("/profile/update", methods=["POST"])
@login_required
def update_profile():
    """Update profile credentials."""
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    new_password = request.form.get("new_password", "").strip()
    avatar_url = request.form.get("avatar_url", "").strip()

    if not username or not email:
        flash("Username and Email are required.", "danger")
        return redirect(url_for("chat_bp.profile"))

    # Validate conflicts
    user_with_username = User.query.filter_by(username=username).first()
    if user_with_username and user_with_username.id != current_user.id:
        flash("Username is already taken.", "danger")
        return redirect(url_for("chat_bp.profile"))

    user_with_email = User.query.filter_by(email=email).first()
    if user_with_email and user_with_email.id != current_user.id:
        flash("Email is already registered.", "danger")
        return redirect(url_for("chat_bp.profile"))

    current_user.username = username
    current_user.email = email
    
    if avatar_url:
        current_user.avatar_url = avatar_url

    if new_password:
        current_user.set_password(new_password)

    db.session.commit()
    flash("Profile updated successfully!", "success")
    return redirect(url_for("chat_bp.profile"))
