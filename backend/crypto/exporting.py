import base64
import json
import os
from typing import Any

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

EXPORT_VERSION = 1
EXPORT_ITERATIONS = 390_000
EXPORT_SALT_SIZE = 16
EXPORT_NONCE_SIZE = 12


def _b64encode(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")


def _b64decode(data: str) -> bytes:
    return base64.b64decode(data.encode("utf-8"))


def _derive_export_key(passphrase: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=EXPORT_ITERATIONS,
    )
    return kdf.derive(passphrase.encode("utf-8"))


def encrypt_export_payload(payload: dict[str, Any], passphrase: str) -> dict[str, Any]:
    salt = os.urandom(EXPORT_SALT_SIZE)
    nonce = os.urandom(EXPORT_NONCE_SIZE)
    key = _derive_export_key(passphrase, salt)
    plaintext = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, None)
    return {
        "version": EXPORT_VERSION,
        "kdf": "PBKDF2-HMAC-SHA256",
        "iterations": EXPORT_ITERATIONS,
        "salt": _b64encode(salt),
        "nonce": _b64encode(nonce),
        "ciphertext": _b64encode(ciphertext),
    }


def decrypt_export_payload(envelope: dict[str, Any], passphrase: str) -> dict[str, Any]:
    if envelope.get("version") != EXPORT_VERSION:
        raise ValueError("Phiên bản file không được hỗ trợ.")
    salt = _b64decode(envelope["salt"])
    nonce = _b64decode(envelope["nonce"])
    ciphertext = _b64decode(envelope["ciphertext"])
    key = _derive_export_key(passphrase, salt)
    plaintext = AESGCM(key).decrypt(nonce, ciphertext, None)
    return json.loads(plaintext.decode("utf-8"))
