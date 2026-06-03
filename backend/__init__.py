import os
from pathlib import Path

from flask import Flask
from dotenv import load_dotenv

from .routes import register_routes

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'data'))
os.makedirs(DATA_DIR, exist_ok=True)


def create_app() -> Flask:
    # Ensure Flask finds the top-level `templates/` and `static/` directories
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    template_folder = os.path.join(project_root, "templates")
    static_folder = os.path.join(project_root, "static")

    # Load .env file from project root if present (convenience for development)
    dotenv_path = os.path.join(project_root, '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path, override=True)
    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
    app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-change-me')
    # Allow overriding the DB path/URL via env var `DATABASE_URL`.
    # Use a sqlite file by default, or a mysql://... URL to connect to MySQL.
    db_path = os.environ.get('DATABASE_URL', os.path.join(DATA_DIR, 'vault.db'))
    register_routes(app, db_path)
    return app
