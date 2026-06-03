import base64
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

SALT_SIZE = 16
KEY_LENGTH = 32
PBKDF2_ITERATIONS = 480_000


def _encode_bytes(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")


def _decode_bytes(data: str) -> bytes:
    return base64.b64decode(data.encode("utf-8"))


def generate_salt() -> bytes:
    """Generate a random salt for password hashing."""
    return os.urandom(SALT_SIZE)


def hash_master_password(password: str, salt: bytes) -> str:
    """Hash a master password using PBKDF2."""
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
    """Verify a master password against its stored hash."""
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
    """Derive the master encryption key from password and salt."""
    password_bytes = password.encode("utf-8")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LENGTH,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return kdf.derive(password_bytes)
