def password_strength(password: str) -> tuple[str, str, dict]:
    if not password:
        return ("Không có mật khẩu", "strength-neutral", {"length": 0})

    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_sym = any(not c.isalnum() for c in password)
    length = len(password)
    categories = sum([has_lower, has_upper, has_digit, has_sym])

    if length >= 14 and categories >= 4:
        label = "Mạnh"
        css = "strength-strong"
    elif length >= 10 and categories >= 3:
        label = "Trung bình"
        css = "strength-medium"
    else:
        label = "Yếu"
        css = "strength-weak"

    details = {
        "length": length,
        "has_lower": has_lower,
        "has_upper": has_upper,
        "has_digit": has_digit,
        "has_sym": has_sym,
        "categories": categories,
    }
    return (label, css, details)
