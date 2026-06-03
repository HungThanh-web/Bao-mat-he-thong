import os

from flask import Flask
from routes import register_routes

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")
DB_PATH = "vault.db"
register_routes(app, DB_PATH)


if __name__ == "__main__":
    app.run(debug=True)
