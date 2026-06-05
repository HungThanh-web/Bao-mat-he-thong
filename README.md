# 🔐 Mini Password Vault

> Ứng dụng quản lý mật khẩu bảo mật với mô-đun mã hóa AES-256-GCM và xác thực 2 lớp (2FA/TOTP).

---

## 📂 Cấu trúc thư mục dự án

```text
Bao-mat-he-thong/
│
├── backend/
│   ├── crypto/                 # Module xử lý mật mã học
│   │   ├── __init__.py
│   │   ├── encryption.py       # Mã hóa/Giải mã AES-256-GCM
│   │   ├── hashing.py          # Băm mật khẩu PBKDF2
│   │   ├── strength.py         # Kiểm tra độ mạnh mật khẩu
│   │   └── totp.py             # Xử lý mã xác thực 2FA/TOTP
│   │
│   ├── __init__.py             # Khởi tạo Flask app và cấu hình DB
│   ├── db.py                   # Cấu hình cơ sở dữ liệu SQLite/MySQL
│   └── routes.py               # Định nghĩa các routes và logic điều hướng
│
├── scripts/                    # Các script bổ trợ
├── static/
│   ├── script.js
│   └── style.css
│
├── templates/
│   ├── add_edit.html
│   ├── audit.html
│   ├── dashboard.html
│   ├── login.html
│   ├── otp.html
│   └── register.html
│
├── .env                        # ⚠️ KHÔNG commit file này lên GitHub!
├── .env.example                # File mẫu cấu hình môi trường (commit cái này)
├── app.py                      # File chạy chính
└── requirements.txt
```

---

## ✨ Tính năng chính

- **Đăng ký / Đăng nhập** — Xác thực tài khoản dựa trên Master Password
- **Mã hóa dữ liệu** — AES-256-GCM mã hóa mật khẩu trước khi lưu vào database
- **Xác thực 2 lớp (2FA)** — OTP dựa trên thời gian (TOTP), đổi mỗi 30 giây
- **Quản lý Credential** — Thêm / Sửa / Xóa tài khoản dịch vụ, mật khẩu ẩn mặc định trên Dashboard

---

## 🚀 Hướng dẫn cài đặt

### Bước 1 — Cài đặt Python

Tải Python 3.8+ tại [python.org](https://python.org).

> ⚠️ Trên Windows: Tích chọn **"Add Python.exe to PATH"** trong lúc cài đặt.

### Bước 2 — Tải mã nguồn và cài thư viện

```powershell
cd "đường_dẫn_đến_thư_mục_dự_án"
python -m pip install -r requirements.txt
```

---

## ⚙️ Cấu hình môi trường (File `.env`)

Tạo file `.env` ở thư mục gốc dự án dựa theo file `.env.example`:

```plaintext
# === Aiven MySQL Configuration ===
DB_HOST=<your-db-host>
DB_PORT=<your-db-port>
DB_USER=<your-db-user>
DB_PASSWORD=<your-db-password>
DB_NAME=<your-db-name>
MYSQL_SSL_CA=ca.pem

# === Flask Configuration ===
FLASK_SECRET_KEY=<your-secret-key>
```

> ⚠️ **KHÔNG commit file `.env` lên GitHub.** File này chứa thông tin đăng nhập database và secret key — chỉ commit file `.env.example` (đã ẩn giá trị thật).

### Giải thích các biến cấu hình

| Biến | Ý nghĩa |
|---|---|
| `DB_HOST` | Địa chỉ server database (Aiven Cloud hoặc localhost) |
| `DB_PORT` | Cổng kết nối database |
| `DB_USER` | Tên đăng nhập database |
| `DB_PASSWORD` | Mật khẩu database — **giữ bí mật tuyệt đối** |
| `DB_NAME` | Tên database sử dụng |
| `MYSQL_SSL_CA` | Đường dẫn file chứng chỉ SSL (Aiven yêu cầu kết nối SSL) |
| `FLASK_SECRET_KEY` | Khóa bí mật Flask dùng để mã hóa session người dùng |

> **Môi trường dev:** có thể dùng chuỗi tạm bất kỳ cho `FLASK_SECRET_KEY`.
> **Môi trường production:** bắt buộc dùng chuỗi ngẫu nhiên dài, phức tạp để tránh giả mạo cookie/session.

---

## 🏃 Chạy ứng dụng

```powershell
python app.py
```

Mở trình duyệt và truy cập:

```
http://127.0.0.1:5000
```

---

## 🖥️ Hướng dẫn sử dụng web

1. Mở trang `http://127.0.0.1:5000` trên trình duyệt.
2. Nếu chưa có tài khoản, bấm vào `Đăng ký` để tạo tài khoản mới.
3. Điền `username`, `password` và `confirm password`, rồi nhấn `Đăng ký`.
4. Sau khi đăng ký thành công, đăng nhập bằng `username` và `password`.
5. Nếu tài khoản được cấu hình TOTP, hệ thống sẽ chuyển tới trang nhập mã OTP.
6. Trên trang `Dashboard`, bạn sẽ thấy danh sách các credential đã lưu.
   - Mật khẩu sẽ được **ẩn mặc định** để tăng riêng tư.
   - Nhấn `Hiện` để xem mật khẩu thực tế, hoặc `Ẩn` để che lại.
7. Để thêm credential mới, vào `Thêm` và điền `service`, `account`, `password`.
8. Để sửa một mục, nhấn `Sửa` trên dòng tương ứng và cập nhật thông tin.
9. Để xóa một mục, nhấn `Xóa` ở mục tương ứng.
10. Đăng xuất bằng nút `Đăng xuất`.

---

## 🔑 Chính sách kiểm tra mật khẩu (Password Policy)

### Quy tắc 1 — Độ mạnh tối thiểu

Mật khẩu phải đáp ứng **tất cả** các tiêu chí sau:

- Tối thiểu **8 ký tự**
- Có ít nhất **1 chữ hoa** (A–Z)
- Có ít nhất **1 chữ số** (0–9)
- Có ít nhất **1 ký tự đặc biệt** (`!@#$%^&*`)

### Quy tắc 2 — Danh sách mật khẩu bị cấm

Hệ thống từ chối 10 mật khẩu phổ biến nhất *(nguồn: NordPass 2024–2025, phân tích 15 tỷ mật khẩu bị lộ)*:

| # | Mật khẩu | Lý do nguy hiểm |
|---|---|---|
| 1 | `123456` | Dùng 21 triệu lần, crack < 1 giây |
| 2 | `admin` | Mặc định hệ thống, crack < 1 giây |
| 3 | `12345678` | Dãy số, crack < 1 giây |
| 4 | `123456789` | Dãy số, crack < 1 giây |
| 5 | `12345` | Dãy số ngắn, crack < 1 giây |
| 6 | `password` | Từ phổ biến nhất, crack < 1 giây |
| 7 | `qwerty` | Pattern bàn phím, crack < 1 giây |
| 8 | `abc123` | Kết hợp đơn giản, crack < 1 giây |
| 9 | `111111` | Lặp ký tự, crack < 1 giây |
| 10 | `iloveyou` | Cụm từ phổ biến, crack < 1 giây |

---

## 🛡️ Xác minh Master Password khi xem / copy mật khẩu

Để ngăn trường hợp kẻ lạ ngồi vào máy đang đăng nhập sẵn rồi xem trộm, hệ thống áp dụng lớp bảo vệ bổ sung:

- Trước khi **hiển thị** hoặc **copy** bất kỳ mật khẩu nào, người dùng phải nhập lại Master Password để xác nhận danh tính.
- Yêu cầu xác minh xuất hiện **mỗi lần** thao tác — không lưu trạng thái đã xác minh trong phiên làm việc.
- Nếu nhập sai Master Password, thao tác bị từ chối và ghi vào Audit Log.

**Luồng xác minh:**

1. Người dùng nhấn `Hiện` hoặc `Copy` trên Dashboard.
2. Hộp thoại yêu cầu nhập lại Master Password xuất hiện.
3. Hệ thống kiểm tra hash — nếu đúng, thực hiện thao tác.
4. Nếu sai, hiển thị thông báo lỗi và ghi log.

---

## 🚧 Tính năng đang phát triển

Một số tính năng hiện đang trong quá trình hoàn thiện — lưu ý để tránh nhầm lẫn khi thử nghiệm:

| Tính năng | Trạng thái | Ghi chú |
|---|---|---|
| TOTP / 2FA Setup | 🔧 Đang phát triển | Luồng thiết lập và QR code chưa hoàn chỉnh |
| QR Code hiển thị | 🔧 Đang phát triển | Sẽ tích hợp sau khi TOTP hoàn thiện |
| Audit Log | ✅ Hoàn thành | Ghi lại mọi thao tác đăng nhập và truy cập |
| Xác minh Master Password | 🔧 Đang phát triển | Xác minh lại trước khi xem/copy mật khẩu |

---

## 🔐 Lưu ý bảo mật

- File `.env` chứa thông tin nhạy cảm — **không bao giờ** chia sẻ công khai.
- Nếu lỡ commit hoặc lộ mật khẩu database, hãy **đổi mật khẩu ngay** trên trang quản trị Aiven.
- Đảm bảo file `.env` đã được thêm vào `.gitignore` trước khi push lên GitHub.
- `FLASK_SECRET_KEY` trong production phải là chuỗi ngẫu nhiên mạnh — có thể sinh bằng lệnh:

```python
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 📦 Thư viện sử dụng

| Thư viện | Mục đích |
|---|---|
| `Flask` | Web framework |
| `cryptography` | AES-256-GCM, PBKDF2 |
| `pyotp` | Sinh và xác thực mã TOTP (2FA) |
| `python-dotenv` | Đọc biến từ file `.env` |
| `PyMySQL` | Kết nối MySQL (nếu dùng Aiven) |
