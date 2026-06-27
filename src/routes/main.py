"""
src/routes/main.py — Public SaaS Pages
=====================================
Serves index landing pages, about info, pricing, and contact pages.
"""

from flask import Blueprint, render_template

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    """Render SaaS landing home page."""
    return render_template("index.html")

@main_bp.route("/about")
def about():
    """Render product overview details page."""
    return render_template("about.html")
