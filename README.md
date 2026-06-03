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
- Mật khẩu trên Dashboard được ẩn mặc định và có thể hiển thị theo nhu cầu
- Hỗ trợ 2FA/TOTP nếu người dùng có `totp_secret`
  - TOTP là mã OTP dựa trên thời gian (thường đổi mỗi 30 giây) giúp xác thực hai yếu tố.

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

Ứng dụng mặc định dùng SQLite và tạo file `data/vault.db` tự động khi không có `DATABASE_URL`.

Nếu bạn đã cấu hình `DATABASE_URL` để dùng MySQL (ví dụ Aiven), thì ứng dụng sẽ chỉ sử dụng MySQL và không dùng `data/vault.db`.

Nếu muốn dùng MySQL, bạn có thể cấu hình bằng biến môi trường hoặc file `.env`.

### Cấu hình dùng biến môi trường

```powershell
$env:DATABASE_URL = "mysql://<user>:<password>@<host>:<port>/<database>?ssl-mode=REQUIRED"
$env:MYSQL_SSL_CA = "C:\\path\\to\\aiven-ca-bundle.pem"
$env:FLASK_SECRET_KEY = "một_chuỗi_bí_mật_mạnh"
```

### Cấu hình dùng `.env`

Tạo file `.env` ở thư mục gốc dự án với nội dung:

```text
DATABASE_URL=mysql://<user>:<password>@<host>:<port>/<database>?ssl-mode=REQUIRED
MYSQL_SSL_CA=C:\path\to\aiven-ca-bundle.pem
FLASK_SECRET_KEY=change-me-to-a-secure-secret
```

Ứng dụng sẽ tự động load `.env` nếu file này tồn tại.

### Kết nối Aiven MySQL

Với thông tin Aiven của bạn, sử dụng giá trị sau:

- `host`: `cyber-security-st-4110.l.aivencloud.com`
- `port`: `20380`
- `database`: `defaultdb`
- `user`: `avnadm`
- `password`: (mật khẩu bạn thấy trong Aiven)
- `ssl-mode`: `REQUIRED`

Ví dụ cấu hình `DATABASE_URL`:

```text
mysql://avnadm:<your_password>@cyber-security-st-4110.l.aivencloud.com:20380/defaultdb?ssl-mode=REQUIRED
```

Nếu Aiven cung cấp file CA certificate, tải về và lưu trên máy, rồi đặt đường dẫn đó vào `MYSQL_SSL_CA`.

**Rất quan trọng:** hãy thay `CLICK_TO_REVEAL_PASSWORD` bằng mật khẩu thực tế từ Aiven. Nếu bạn để nguyên placeholder hoặc nhập sai mật khẩu, app sẽ không khởi được và sẽ báo lỗi `Access denied`.

Sau đó chạy bình thường:

```powershell
python app.py
```

Nếu kết nối thành công, dữ liệu người dùng và credential sẽ được lưu trong MySQL Aiven.

## Chạy ứng dụng

```powershell
python app.py
```

Mở trình duyệt và truy cập:

```text
http://127.0.0.1:5000
```

## Hướng dẫn sử dụng web

1. Mở trang `http://127.0.0.1:5000`.
2. Nếu chưa có tài khoản, bấm vào `Đăng ký` để tạo tài khoản mới.
3. Điền `username`, `password` và `confirm password`, rồi nhấn `Đăng ký`.
4. Sau khi đăng ký thành công, đăng nhập bằng `username` và `password`.
5. Nếu tài khoản được cấu hình TOTP, hệ thống sẽ chuyển tới trang nhập mã OTP.
6. Trên trang `Dashboard`, bạn sẽ thấy danh sách các credential đã lưu.
   - Mật khẩu sẽ được ẩn mặc định để tăng riêng tư.
   - Nhấn `Hiện` để xem mật khẩu thực tế, hoặc `Ẩn` để che lại.
7. Để thêm credential mới, vào `Thêm` và điền `service`, `account`, `password`.
8. Để sửa một mục, nhấn `Sửa` trên dòng tương ứng và cập nhật thông tin.
9. Để xóa một mục, nhấn `Xóa` ở mục tương ứng.
10. Đăng xuất bằng nút `Đăng xuất`.

## Những chức năng web hiện có

- Đăng ký tài khoản mới
- Đăng nhập
- Xem danh sách credential
- Thêm credential
- Sửa credential
- Xóa credential
- Hỗ trợ TOTP nếu người dùng có `totp_secret`

## Những tính năng còn thiếu hoặc có thể bổ sung

- Chưa có trang `Profile` để người dùng đổi mật khẩu chính hoặc bật/tắt TOTP.
- Chưa có phần nhập mã TOTP khi lần đầu bật 2FA.
- Chưa có tính năng tải xuống/backup credential dưới dạng file mã hóa.
- Chưa có bộ lọc/tìm kiếm credential trên trang Dashboard.
- Chưa có phần quản lý nhiều người dùng hoặc phân quyền.
- Chưa có tính năng tự động xoá session khi đóng trình duyệt.
- Chưa có bước kiểm tra độ mạnh mật khẩu khi đăng ký.

### Tuỳ chọn bổ sung

- `FLASK_SECRET_KEY` — thay đổi giá trị bí mật để bảo mật session khi chạy ứng dụng thực tế.

```powershell
$env:FLASK_SECRET_KEY = "một_chuỗi_bí_mật_mạnh"
```

## Ghi chú

- Đây là ứng dụng demo: master password được dùng để tạo khóa mã hóa và một phiên bản khóa được lưu tạm trong session.
- Nếu triển khai vào thực tế, cần bảo vệ session, cookie, và dữ liệu nhạy cảm tốt hơn.
- Nếu dùng MySQL và cần cấp chứng chỉ, có thể bổ sung cấu hình SSL cho kết nối.
