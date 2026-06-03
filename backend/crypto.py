import base64
import os
from typing import Optional

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import pyotp

SALT_SIZE = 16
KEY_LENGTH = 32
PBKDF2_ITERATIONS = 480_000
AES_NONCE_SIZE = 12


def _encode_bytes(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")


def _decode_bytes(data: str) -> bytes:
    return base64.b64decode(data.encode("utf-8"))


def generate_salt() -> bytes:
    return os.urandom(SALT_SIZE)


def hash_master_password(password: str, salt: bytes) -> str:
    password_bytes = password.encode("utf-8")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LENGTH,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    key = kdf.derive(password_bytes)
    return _encode_bytes(key)


def verify_master_password(password: str, salt: bytes, stored_hash: str) -> bool:
    password_bytes = password.encode("utf-8")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LENGTH,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    try:
        kdf.verify(password_bytes, _decode_bytes(stored_hash))
        return True
    except Exception:
        return False


def derive_master_key(password: str, salt: bytes) -> bytes:
    password_bytes = password.encode("utf-8")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LENGTH,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return kdf.derive(password_bytes)


def encrypt_password(plaintext: str, key: bytes) -> tuple[str, str]:
    aesgcm = AESGCM(key)
    nonce = os.urandom(AES_NONCE_SIZE)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return _encode_bytes(ciphertext), _encode_bytes(nonce)


def decrypt_password(ciphertext_b64: str, nonce_b64: str, key: bytes) -> Optional[str]:
    aesgcm = AESGCM(key)
    ciphertext = _decode_bytes(ciphertext_b64)
    nonce = _decode_bytes(nonce_b64)
    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")
    except InvalidTag:
        return None


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def password_strength(password: str) -> tuple[str, str, dict]:
    """Return (label, css_class, details) for a given plaintext password.

    details includes length and which character classes are present.
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


def get_totp_uri(username: str, secret: str, issuer_name: str = "MiniPasswordVault") -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name=issuer_name)


def verify_totp(secret: str, token: str) -> bool:
    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=1)
