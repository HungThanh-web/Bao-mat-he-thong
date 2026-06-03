# Mini Password Vault

Ứng dụng mẫu quản lý mật khẩu với mô-đun mã hóa và xác thực.

## Những file đã tạo

- `app.py` — tạo Flask app chính và cấu hình ứng dụng
- `routes.py` — định nghĩa các route, logic xác thực và quản lý credential
- `backend/crypto.py` — xử lý mật mã: PBKDF2 hashing, master key derivation, AES-256-GCM encrypt/decrypt, TOTP
- `db.py` — khởi tạo SQLite và CRUD cho người dùng + vault credentials
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
- Lưu trữ dữ liệu người dùng và credential trong SQLite
- Quản lý credential: thêm, sửa, xóa
- Hỗ trợ 2FA/TOTP nếu người dùng có `totp_secret`

## Cài đặt

1. Mở PowerShell hoặc terminal
2. Chuyển đến thư mục dự án:

```powershell
cd /d d:\Bảo_mật_mk
```

3. Cài thư viện:

```powershell
python -m pip install -r requirements.txt
```

## Chạy ứng dụng

```powershell
python app.py
```

Mở trình duyệt và truy cập:

```text
http://127.0.0.1:5000
```

## Ghi chú

- Mục đích của project này là demo kiến thức bảo mật: PBKDF2 + salt, AES-GCM, TOTP, và lưu trữ an toàn.
- Tên file `data/vault.db` sẽ được tạo tự động khi chạy app lần đầu.
- Trong ứng dụng demo, `master_key` được lưu tạm trong session để tiện giải mã. Nếu triển khai thực tế, cần cải tiến lớp bảo mật hơn.
