import os

from flask import Flask

from .routes import register_routes

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'data'))
os.makedirs(DATA_DIR, exist_ok=True)


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-change-me')
    db_path = os.path.join(DATA_DIR, 'vault.db')
    register_routes(app, db_path)
    return app
