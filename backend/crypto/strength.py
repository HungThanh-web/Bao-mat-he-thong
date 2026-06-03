def password_strength(password: str) -> tuple[str, str, dict]:
    """Evaluate password strength.
    
    Args:
        password: The plaintext password to evaluate
    
    Returns:
        Tuple of (label, css_class, details_dict)
        - label: "Mạnh", "Trung bình", or "Yếu"
        - css_class: "strength-strong", "strength-medium", or "strength-weak"
        - details: dict with length and character class info
    """
    if not password:
        return ("Không có mật khẩu", "strength-neutral", {"length": 0})

    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_sym = any(not c.isalnum() for c in password)
    length = len(password)

    categories = sum([has_lower, has_upper, has_digit, has_sym])

    if length >= 12 and categories >= 3:
        label = "Mạnh"
        css = "strength-strong"
    elif length >= 8 and categories >= 2:
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
