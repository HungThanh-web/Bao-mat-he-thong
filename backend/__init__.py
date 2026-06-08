import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask

from .routes import register_routes

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, "data"))
os.makedirs(DATA_DIR, exist_ok=True)


def create_app() -> Flask:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    template_folder = os.path.join(project_root, "templates")
    static_folder = os.path.join(project_root, "static")

    dotenv_path = os.path.join(project_root, ".env")
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path, override=True)

    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")

    app.config["SESSION_PERMANENT"] = False
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=5)
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = os.environ.get("FLASK_ENV") == "production"

    db_path = os.environ.get("DATABASE_URL", os.path.join(DATA_DIR, "vault.db"))
    register_routes(app, db_path)
    return app
