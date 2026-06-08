# Mini Password Vault

Mini Password Vault là ứng dụng Flask dùng để quản lý mật khẩu cá nhân. Ứng dụng cho phép người dùng đăng ký bằng Master Password, lưu các tài khoản dịch vụ trong kho mật khẩu, mã hóa mật khẩu trước khi ghi xuống database, bật xác thực 2 yếu tố và kiểm tra sức khỏe mật khẩu.

## Công nghệ sử dụng

| Thành phần | Mục đích |
|---|---|
| Flask | Web framework, xử lý route và render giao diện |
| MySQL / PyMySQL | Lưu người dùng và dữ liệu vault đã mã hóa |
| cryptography | PBKDF2-HMAC-SHA256 và AES-256-GCM |
| pyotp | Sinh và xác minh mã TOTP cho 2FA |
| qrcode | Tạo ảnh QR code để thiết lập 2FA nhanh bằng Authenticator |
| python-dotenv | Đọc cấu hình từ file `.env` |
| JavaScript | Password generator, copy clipboard, auto-lock phía trình duyệt |

## Cấu trúc thư mục

```text
Bao-mat-he-thong/
├── app.py
├── backend/
│   ├── __init__.py
│   ├── db.py
│   ├── routes.py
│   └── crypto/
│       ├── __init__.py
│       ├── encryption.py
│       ├── exporting.py
│       ├── hashing.py
│       ├── strength.py
│       └── totp.py
├── static/
│   ├── script.js
│   └── style.css
├── templates/
│   ├── add_edit.html
│   ├── audit.html
│   ├── audit_all.html
│   ├── dashboard.html
│   ├── import_export.html
│   ├── login.html
│   ├── otp.html
│   ├── register.html
│   └── setup_2fa.html
├── requirements.txt
├── FEATURES.md
└── .env.example
```

## Kiến trúc bảo mật

### Master Password

Master Password là mật khẩu chính của người dùng. Người dùng chỉ cần nhớ mật khẩu này để đăng nhập vào ứng dụng và mở kho mật khẩu.

Ứng dụng không lưu Master Password dưới dạng văn bản thuần. Khi đăng ký, hệ thống tạo salt ngẫu nhiên và băm Master Password bằng PBKDF2-HMAC-SHA256 với nhiều vòng lặp. Database chỉ lưu `password_hash` và `salt`.

### Khóa mã hóa vault

Từ Master Password và salt, hệ thống dẫn xuất ra khóa 32 byte. Khóa này được dùng để mã hóa và giải mã mật khẩu trong kho vault.

Mỗi mật khẩu trong vault được mã hóa bằng AES-256-GCM với nonce riêng. Database chỉ lưu ciphertext và nonce, không lưu mật khẩu gốc của từng dịch vụ.

### Session và auto-lock

Sau khi đăng nhập, ứng dụng lưu khóa phiên trong session để có thể giải mã vault khi người dùng thao tác. Session phía server có thời gian hết hạn 5 phút. Phía trình duyệt cũng có cơ chế auto-lock: nếu người dùng không hoạt động trong khoảng thời gian cấu hình, trang sẽ tự chuyển tới `/logout`.

## Chức năng cốt lõi

### 1. Đăng ký tài khoản

Người dùng tạo tài khoản bằng tên đăng nhập và Master Password. Khi đăng ký:

- hệ thống kiểm tra tên đăng nhập không bị trống;
- kiểm tra mật khẩu xác nhận trùng khớp;
- tạo salt ngẫu nhiên;
- băm Master Password bằng PBKDF2;
- lưu username, password hash và salt vào bảng `users`.

Ý nghĩa: nếu database bị lộ, kẻ tấn công không nhìn thấy Master Password thật.

### 2. Đăng nhập bằng Master Password

Khi đăng nhập, người dùng nhập username và Master Password. Hệ thống lấy salt của user, băm lại mật khẩu vừa nhập và so sánh với hash đã lưu.

Nếu đúng, hệ thống:

- tạo master key từ Master Password;
- lưu thông tin phiên đăng nhập;
- nếu user đã bật 2FA thì chuyển sang bước nhập OTP;
- nếu chưa bật 2FA thì vào dashboard.

### 3. Quản lý kho mật khẩu

Dashboard hiển thị danh sách credential đã lưu. Mỗi credential có các trường:

- tên ứng dụng hoặc website;
- tên đăng nhập;
- mật khẩu;
- URL website;
- ghi chú;
- danh mục;
- ngày tạo và ngày cập nhật.

Người dùng có thể thêm, xem, sửa và xóa từng credential. Mật khẩu được che mặc định trên dashboard. Người dùng có thể bấm `Hiện` để xem hoặc `Sao chép` để copy.

### 4. Mã hóa mật khẩu từng dịch vụ

Khi thêm hoặc sửa credential, mật khẩu được mã hóa trước khi lưu xuống database.

Luồng xử lý:

1. Người dùng nhập mật khẩu dịch vụ.
2. Server lấy master key trong session.
3. Hệ thống tạo nonce ngẫu nhiên.
4. Mật khẩu được mã hóa bằng AES-256-GCM.
5. Database lưu ciphertext và nonce.

Ý nghĩa: database không chứa mật khẩu gốc của Facebook, Gmail, ngân hàng hoặc các dịch vụ khác.

### 5. Password Generator

Ứng dụng có trình tạo mật khẩu ngẫu nhiên tại màn hình thêm/sửa credential. Người dùng có thể chọn:

- độ dài mật khẩu;
- có chữ hoa hay không;
- có chữ thường hay không;
- có số hay không;
- có ký tự đặc biệt hay không.

Generator dùng `crypto.getRandomValues` trên trình duyệt để tạo số ngẫu nhiên tốt hơn `Math.random`.

## Chức năng bảo mật nâng cao

### 1. Xác thực 2 yếu tố 2FA / TOTP

2FA là lớp xác thực thứ hai sau Master Password. Nếu bật 2FA, người dùng phải nhập thêm mã OTP 6 số từ ứng dụng Authenticator.

Ứng dụng hỗ trợ TOTP, tương thích với:

- Google Authenticator;
- Authy;
- Microsoft Authenticator;
- các ứng dụng TOTP khác.

Luồng bật 2FA:

1. Người dùng vào trang `2FA`.
2. Hệ thống tạo TOTP secret và QR code.
3. Người dùng quét QR code bằng ứng dụng Authenticator.
4. Nếu không quét được QR, người dùng có thể nhập secret hoặc OTP URI thủ công.
5. Ứng dụng Authenticator sinh mã OTP 6 số.
6. Người dùng nhập mã OTP vào web để xác nhận.
7. Nếu mã đúng, hệ thống lưu TOTP secret cho tài khoản.

Luồng đăng nhập khi đã bật 2FA:

1. Nhập username và Master Password.
2. Nếu mật khẩu đúng, hệ thống chuyển tới trang nhập OTP.
3. Người dùng mở app Authenticator để lấy mã 6 số.
4. Nhập đúng mã thì mới vào được dashboard.

Ý nghĩa: nếu ai đó biết Master Password, họ vẫn chưa đăng nhập được nếu không có thiết bị Authenticator.

### 2. Auto-lock

Auto-lock tự khóa ứng dụng khi người dùng không hoạt động. Cơ chế này giảm rủi ro khi người dùng quên đăng xuất trên máy tính.

Ứng dụng có 2 lớp:

- session Flask hết hạn sau 5 phút;
- JavaScript theo dõi hoạt động như click, gõ phím, cuộn trang, chạm màn hình và tự logout khi quá thời gian.

### 3. Bảo vệ clipboard

Khi người dùng bấm `Sao chép`, mật khẩu được copy vào clipboard. Sau 60 giây, ứng dụng cố gắng ghi chuỗi rỗng vào clipboard để xóa mật khẩu đã copy.

Ý nghĩa: giảm nguy cơ ứng dụng khác hoặc người dùng khác đọc lại mật khẩu từ clipboard.

Giới hạn: trình duyệt và hệ điều hành có thể hạn chế quyền clipboard, nên thao tác xóa clipboard không phải lúc nào cũng được đảm bảo tuyệt đối.

### 4. Ẩn mật khẩu khi rời tab

Khi tab trình duyệt bị ẩn hoặc người dùng chuyển sang tab khác, JavaScript tự che lại các mật khẩu đang được hiển thị.

Ý nghĩa: hạn chế việc mật khẩu vẫn nằm lộ trên màn hình khi người dùng chuyển việc hoặc rời máy.

### 5. Cookie bảo mật

Session cookie được cấu hình:

- `HttpOnly`: JavaScript không đọc được cookie phiên;
- `SameSite=Lax`: giảm rủi ro CSRF trong các luồng thông thường;
- `Secure` khi chạy môi trường production qua HTTPS.

## Chức năng nâng cao trải nghiệm

### 1. Tìm kiếm nhanh

Dashboard có ô tìm kiếm để lọc credential theo:

- tên dịch vụ;
- tên tài khoản;
- URL;
- ghi chú.

Tính năng này giúp tìm nhanh một mật khẩu khi vault có nhiều mục.

### 2. Phân loại theo danh mục

Mỗi credential có trường danh mục, ví dụ:

- Cá nhân;
- Công việc;
- Tài chính;
- Mạng xã hội.

Dashboard có bộ lọc danh mục để người dùng quản lý dữ liệu dễ hơn.

### 3. Ghi chú và URL

Ngoài username/password, mỗi credential có thể lưu URL và ghi chú. URL giúp mở đúng website cần đăng nhập. Ghi chú có thể dùng để lưu thông tin phụ như email khôi phục, câu hỏi bảo mật hoặc ghi chú nội bộ.

### 4. Hiện / ẩn mật khẩu

Mật khẩu trong dashboard được che mặc định bằng dấu chấm. Người dùng có thể bấm `Hiện` để xem nhanh và bấm `Ẩn` để che lại.

### 5. Import / Export dữ liệu

Ứng dụng hỗ trợ xuất và nhập vault bằng file JSON được mã hóa.

Khi export:

1. Người dùng nhập passphrase riêng cho file export.
2. Hệ thống giải mã vault trong phiên hiện tại.
3. Dữ liệu export được mã hóa lại bằng AES-GCM.
4. File tải về có dạng `mini-password-vault.enc.json`.

Khi import:

1. Người dùng chọn file `.enc.json`.
2. Nhập passphrase đã dùng khi export.
3. Hệ thống giải mã file.
4. Từng credential được mã hóa lại bằng master key của tài khoản hiện tại rồi lưu vào database.

Ý nghĩa: người dùng có thể sao lưu hoặc chuyển dữ liệu giữa các tài khoản mà không lưu file plaintext.

## Chức năng giám sát và phục hồi

### 1. Password Audit toàn kho

Trang audit toàn kho giúp đánh giá sức khỏe mật khẩu. Ứng dụng thống kê:

- số mật khẩu yếu;
- số mật khẩu bị trùng;
- số mật khẩu đã quá 180 ngày.

Mục tiêu là giúp người dùng biết credential nào nên đổi trước.

### 2. Kiểm tra độ mạnh mật khẩu

Ứng dụng đánh giá mật khẩu theo:

- độ dài;
- có chữ thường;
- có chữ hoa;
- có số;
- có ký tự đặc biệt;
- số nhóm ký tự được sử dụng.

Kết quả được chia thành:

- `Mạnh`;
- `Trung bình`;
- `Yếu`.

### 3. Phát hiện mật khẩu trùng lặp

Audit giải mã các mật khẩu trong vault của người dùng và so sánh nội bộ để phát hiện các mục dùng cùng một mật khẩu.

Ý nghĩa: nếu một dịch vụ bị lộ mật khẩu, các tài khoản khác dùng cùng mật khẩu cũng có nguy cơ bị chiếm.

### 4. Cảnh báo mật khẩu cũ

Ứng dụng đánh dấu mật khẩu đã quá 180 ngày kể từ lần tạo hoặc cập nhật gần nhất.

Ý nghĩa: nhắc người dùng thay đổi mật khẩu định kỳ cho các tài khoản quan trọng.

### 5. Kiểm tra rò rỉ dữ liệu với Have I Been Pwned

Ứng dụng có chức năng kiểm tra mật khẩu với Have I Been Pwned Pwned Passwords API.

Ứng dụng không gửi mật khẩu gốc lên API. Thay vào đó:

1. Hệ thống băm mật khẩu bằng SHA-1.
2. Chỉ gửi 5 ký tự đầu của hash lên API.
3. API trả về danh sách các suffix có cùng prefix.
4. Ứng dụng so khớp phần suffix còn lại ở phía server.

Mô hình này gọi là k-anonymity, giúp kiểm tra rò rỉ mà không gửi toàn bộ mật khẩu hoặc toàn bộ hash ra ngoài.

## Hướng dẫn cài đặt

### 1. Cài Python

Cài Python 3.10+ từ [python.org](https://python.org).

Trên Windows, nên chọn `Add Python.exe to PATH` khi cài đặt.

### 2. Cài thư viện

```powershell
python -m pip install -r requirements.txt
```

### 3. Cấu hình môi trường

Tạo file `.env` ở thư mục gốc dựa trên `.env.example`.

```plaintext
DB_HOST=<your-db-host>
DB_PORT=<your-db-port>
DB_USER=<your-db-user>
DB_PASSWORD=<your-db-password>
DB_NAME=<your-db-name>
MYSQL_SSL_CA=ca.pem

FLASK_SECRET_KEY=<your-secret-key>
```

Giải thích:

| Biến | Ý nghĩa |
|---|---|
| `DB_HOST` | Địa chỉ MySQL server |
| `DB_PORT` | Cổng kết nối MySQL |
| `DB_USER` | Tên đăng nhập database |
| `DB_PASSWORD` | Mật khẩu database |
| `DB_NAME` | Tên database |
| `MYSQL_SSL_CA` | File CA nếu MySQL yêu cầu SSL |
| `FLASK_SECRET_KEY` | Khóa bí mật để ký session Flask |

Không commit file `.env` lên GitHub vì file này chứa thông tin nhạy cảm.

### 4. Chạy ứng dụng

```powershell
python app.py
```

Mở trình duyệt:

```text
http://127.0.0.1:5000
```

## Hướng dẫn sử dụng nhanh

1. Truy cập `/register` để tạo tài khoản.
2. Đăng nhập bằng username và Master Password.
3. Vào `Thêm` để lưu credential đầu tiên.
4. Dùng `Tạo` để sinh mật khẩu mạnh nếu cần.
5. Trên dashboard, dùng tìm kiếm hoặc lọc danh mục để quản lý vault.
6. Vào `2FA` để bật xác thực 2 yếu tố.
7. Vào `Audit` để kiểm tra mật khẩu yếu, trùng hoặc quá cũ.
8. Dùng `Export` để sao lưu vault thành file mã hóa.
9. Dùng `Import` để nhập lại file export đã mã hóa.

## Lưu ý bảo mật

- Luôn dùng `FLASK_SECRET_KEY` dài, ngẫu nhiên và riêng cho production.
- Luôn chạy production qua HTTPS để bảo vệ cookie và dữ liệu truyền trên mạng.
- Không chia sẻ file `.env`, file export hoặc passphrase export.
- Nếu nghi ngờ database credential bị lộ, hãy đổi mật khẩu database ngay.
- Nếu HIBP báo mật khẩu đã rò rỉ, hãy đổi mật khẩu đó trên dịch vụ gốc và cập nhật lại vault.

## Giới hạn hiện tại

Một số chức năng trong danh sách mục tiêu cần nền tảng hoặc kiến trúc riêng, chưa thể đảm bảo hoàn chỉnh trong ứng dụng Flask web thuần:

| Chức năng | Trạng thái | Lý do |
|---|---|---|
| Zero-knowledge client-side encryption tuyệt đối | Chưa hoàn chỉnh | Server hiện vẫn nhận Master Password khi đăng nhập và giữ master key trong session để render vault |
| Autofill trình duyệt | Chưa có | Cần browser extension riêng |
| Đăng nhập sinh trắc học | Chưa có | Cần WebAuthn/passkey hoặc ứng dụng mobile/native |
| Chống chụp màn hình tuyệt đối | Chưa có | Web browser không có quyền chặn screenshot ở mức hệ điều hành |
| OTP qua email/SMS | Chưa có | Cần hạ tầng gửi email/SMS và kiểm soát abuse |

## Ghi chú về zero-knowledge

Ứng dụng đã mã hóa dữ liệu vault trong database, nhưng chưa đạt zero-knowledge đúng nghĩa như các password manager chuyên nghiệp. Để đạt mức đó, cần chuyển mã hóa/giải mã sang trình duyệt bằng WebCrypto, server chỉ lưu ciphertext và không bao giờ nhận Master Password hoặc master key.

Thiết kế hiện tại phù hợp cho bài thực hành bảo mật và ứng dụng quản lý mật khẩu cơ bản, nhưng chưa nên xem là kiến trúc production-grade cho dữ liệu cực kỳ nhạy cảm.
