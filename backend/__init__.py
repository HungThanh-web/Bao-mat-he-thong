import os
import secrets
from pathlib import Path
from datetime import timedelta  # Thêm thư viện này để cấu hình thời gian phiên

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
    
    # Lấy Secret Key bảo mật từ .env, nếu không có sẽ generate random key
    secret_key = os.environ.get('FLASK_SECRET_KEY')
    if not secret_key:
        secret_key = secrets.token_hex(32)
        print(f"⚠️  WARNING: FLASK_SECRET_KEY not set in .env. Generated random key.")
        print(f"⚠️  Add to .env: FLASK_SECRET_KEY={secret_key}")
    app.secret_key = secret_key
    
    # ----------------------------------------------------------------------
    # 🔒 CẤU HÌNH BẢO MẬT PHIÊN (SESSION SECURITY) - SỬA LỖI ĐĂNG XUẤT
    # ----------------------------------------------------------------------
    # Ép Cookie tự hủy ngay khi người dùng tắt hẳn trình duyệt (Bấm dấu X)
    app.config['SESSION_PERMANENT'] = False 
    
    # Thiết lập thời gian hết hạn (Session Timeout) sau 30 phút nếu không tương tác
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
    
    # Tăng cường bảo mật Cookie, chống các cuộc tấn công Cross-Site Scripting (XSS)
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    # ----------------------------------------------------------------------

    # Cấu hình DB path/URL từ biến môi trường
    db_path = os.environ.get('DATABASE_URL', os.path.join(DATA_DIR, 'vault.db'))
    
    register_routes(app, db_path)
    return app