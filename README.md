# Mini Password Vault

Ứng dụng mẫu quản lý mật khẩu với mô-đun mã hóa và xác thực.

## Những file đã tạo

- `app.py` — tạo Flask app chính và cấu hình ứng dụng
- `backend/__init__.py` — khởi tạo Flask app và cấu hình đường dẫn DB
- `backend/routes.py` — định nghĩa các route, logic xác thực và quản lý credential
- `backend/crypto.py` — xử lý mật mã: PBKDF2 hashing, master key derivation, AES-256-GCM encrypt/decrypt, TOTP
- `backend/db.py` — khởi tạo SQLite/MySQL và CRUD cho người dùng + vault credentials
- `requirements.txt` — danh sách thư viện cần cài
- `README.md` — tài liệu hướng dẫn sử dụng
- `templates/` — giao diện HTML cho các trang:
  - `login.html`
  - `register.html`
  - `otp.html`
  - `dashboard.html`
  - `add_edit.html`
- `static/style.css` — kiểu dáng cơ bản cho toàn bộ ứng dụng

## Tính năng chính

- Đăng ký tài khoản mới với Master Password
- Đăng nhập và xác thực Master Password
- Mã hóa mật khẩu dịch vụ bằng AES-256-GCM trước khi lưu
- Lưu trữ dữ liệu người dùng và credential trong SQLite hoặc MySQL
- Quản lý credential: thêm, sửa, xóa
- Hỗ trợ 2FA/TOTP nếu người dùng có `totp_secret`

## Cài đặt

1. Mở PowerShell hoặc terminal
2. Chuyển đến thư mục dự án:

```powershell
cd /d "C:\Users\admin\Documents\GitHub\Bảo mật hệ thống"
```

3. Cài thư viện:

```powershell
python -m pip install -r requirements.txt
```

## Cấu hình DB

Ứng dụng mặc định dùng SQLite và tạo file `data/vault.db` tự động.

Nếu muốn dùng MySQL, thiết lập biến môi trường `DATABASE_URL` như sau:

```powershell
$env:DATABASE_URL = "mysql://<user>:<password>@<host>:<port>/<database>?ssl-mode=REQUIRED"
```

Sau đó chạy ứng dụng bình thường.

## Chạy ứng dụng

```powershell
python app.py
```

Mở trình duyệt và truy cập:

```text
http://127.0.0.1:5000
```

### Tuỳ chọn bổ sung

- `FLASK_SECRET_KEY` — thay đổi giá trị bí mật để bảo mật session khi chạy ứng dụng thực tế.

```powershell
$env:FLASK_SECRET_KEY = "một_chuỗi_bí_mật_mạnh"
```

## Ghi chú

- Đây là ứng dụng demo: master password được dùng để tạo khóa mã hóa và một phiên bản khóa được lưu tạm trong session.
- Nếu triển khai vào thực tế, cần bảo vệ session, cookie, và dữ liệu nhạy cảm tốt hơn.
- Nếu dùng MySQL và cần cấp chứng chỉ, có thể bổ sung cấu hình SSL cho kết nối.
