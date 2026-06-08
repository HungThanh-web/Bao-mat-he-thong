# Trạng thái tính năng Password Manager

## Đã triển khai trong ứng dụng Flask

- Đăng ký / đăng nhập bằng Master Password, hash bằng PBKDF2-HMAC-SHA256 kèm salt.
- Mã hóa mật khẩu vault bằng AES-256-GCM trước khi lưu database.
- CRUD credential với tên dịch vụ, tài khoản, mật khẩu, URL, ghi chú và danh mục.
- Password generator có tùy chọn độ dài, chữ hoa, chữ thường, số và ký tự đặc biệt.
- TOTP 2FA: bật, xác minh khi đăng nhập và tắt 2FA.
- Auto-lock: trình duyệt tự chuyển tới logout sau thời gian không hoạt động, session server hết hạn sau 5 phút.
- Clipboard protection: sau khi copy mật khẩu, ứng dụng cố gắng xóa clipboard sau 60 giây.
- Tìm kiếm và lọc theo danh mục.
- Password audit: cảnh báo mật khẩu yếu, trùng lặp và quá 180 ngày.
- Breach alert: kiểm tra mật khẩu qua Have I Been Pwned Pwned Passwords API bằng mô hình k-anonymity.
- Import/export file JSON được mã hóa bằng passphrase riêng.

## Giới hạn hiện tại

- Zero-knowledge tuyệt đối chưa hoàn chỉnh vì server Flask vẫn nhận Master Password khi đăng nhập và giữ master key trong session để render vault. Để đạt client-side encryption đúng nghĩa cần chuyển thao tác mã hóa/giải mã sang WebCrypto ở trình duyệt hoặc dùng giao thức xác thực không gửi mật khẩu thô lên server.
- Autofill trình duyệt cần browser extension riêng.
- Đăng nhập sinh trắc học và chống screenshot cần ứng dụng mobile/native hoặc WebAuthn/passkey, không thể đảm bảo bằng Flask web thuần.
- OTP qua SMS/email cần hạ tầng gửi tin nhắn/email và chống abuse.
