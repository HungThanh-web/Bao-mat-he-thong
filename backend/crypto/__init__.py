"""Crypto module - unified import interface for all cryptographic functions."""

# Re-export for backward compatibility
from backend.crypto.hashing import (
    generate_salt,
    hash_master_password,
    verify_master_password,
    derive_master_key,
    SALT_SIZE,
    KEY_LENGTH,
    PBKDF2_ITERATIONS,
)
from backend.crypto.encryption import (
    encrypt_password,
    decrypt_password,
    AES_NONCE_SIZE,
)
from backend.crypto.totp import (
    generate_totp_secret,
    get_totp_uri,
    verify_totp,
)
from backend.crypto.strength import (
    password_strength,
)

__all__ = [
    # Hashing
    "generate_salt",
    "hash_master_password",
    "verify_master_password",
    "derive_master_key",
    # Encryption
    "encrypt_password",
    "decrypt_password",
    # TOTP
    "generate_totp_secret",
    "get_totp_uri",
    "verify_totp",
    # Strength
    "password_strength",
    # Constants
    "SALT_SIZE",
    "KEY_LENGTH",
    "PBKDF2_ITERATIONS",
    "AES_NONCE_SIZE",
]
