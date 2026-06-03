import pyotp


def generate_totp_secret() -> str:
    """Generate a new TOTP secret (base32 encoded)."""
    return pyotp.random_base32()


def get_totp_uri(username: str, secret: str, issuer_name: str = "MiniPasswordVault") -> str:
    """Get the provisioning URI for TOTP QR code generation.
    
    Args:
        username: The user's username
        secret: The TOTP secret
        issuer_name: The issuer name (app name)
    
    Returns:
        otpauth:// URI for QR code generation
    """
    return pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name=issuer_name)


def verify_totp(secret: str, token: str) -> bool:
    """Verify a TOTP token.
    
    Args:
        secret: The TOTP secret
        token: The 6-digit code to verify
    
    Returns:
        True if token is valid, False otherwise
    """
    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=1)
