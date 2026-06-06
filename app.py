import os
from backend import create_app

app = create_app()

if __name__ == "__main__":
    # Chỉ bật debug mode nếu FLASK_ENV=development
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug_mode)
