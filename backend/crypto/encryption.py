import base64
import os
from typing import Optional
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

AES_NONCE_SIZE = 12


def _encode_bytes(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")


def _decode_bytes(data: str) -> bytes:
    return base64.b64decode(data.encode("utf-8"))


def encrypt_password(plaintext: str, key: bytes) -> tuple[str, str]:
    """Encrypt a password using AES-256-GCM.
    
    Args:
        plaintext: The plaintext password to encrypt
        key: The 32-byte encryption key
    
    Returns:
        Tuple of (ciphertext_b64, nonce_b64)
    """
    aesgcm = AESGCM(key)
    nonce = os.urandom(AES_NONCE_SIZE)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return _encode_bytes(ciphertext), _encode_bytes(nonce)


def decrypt_password(ciphertext_b64: str, nonce_b64: str, key: bytes) -> Optional[str]:
    """Decrypt a password using AES-256-GCM.
    
    Args:
        ciphertext_b64: Base64-encoded ciphertext
        nonce_b64: Base64-encoded nonce
        key: The 32-byte encryption key
    
    Returns:
        Plaintext password or None if decryption fails
    """
    aesgcm = AESGCM(key)
    ciphertext = _decode_bytes(ciphertext_b64)
    nonce = _decode_bytes(nonce_b64)
    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")
    except InvalidTag:
        return None
