import sqlite3
from typing import Any, Dict, List, Optional

DB_SCHEMA = [
    "CREATE TABLE IF NOT EXISTS users ("
    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
    "username TEXT UNIQUE NOT NULL, "
    "password_hash TEXT NOT NULL, "
    "salt TEXT NOT NULL, "
    "totp_secret TEXT"
    ")",
    "CREATE TABLE IF NOT EXISTS vault_credentials ("
    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
    "user_id INTEGER NOT NULL, "
    "service TEXT NOT NULL, "
    "account TEXT NOT NULL, "
    "encrypted_password TEXT NOT NULL, "
    "nonce TEXT NOT NULL, "
    "created_at TEXT DEFAULT CURRENT_TIMESTAMP, "
    "FOREIGN KEY(user_id) REFERENCES users(id)"
    ")",
]


def _dict_factory(cursor: sqlite3.Cursor, row: sqlite3.Row) -> Dict[str, Any]:
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def get_connection(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = _dict_factory
    return conn


def init_db(path: str) -> None:
    conn = get_connection(path)
    with conn:
        for statement in DB_SCHEMA:
            conn.execute(statement)
    conn.close()


def create_user(path: str, username: str, password_hash: str, salt: str, totp_secret: Optional[str] = None) -> int:
    conn = get_connection(path)
    with conn:
        cursor = conn.execute(
            "INSERT INTO users (username, password_hash, salt, totp_secret) VALUES (?, ?, ?, ?)",
            (username, password_hash, salt, totp_secret),
        )
    conn.close()
    return cursor.lastrowid


def get_user_by_username(path: str, username: str) -> Optional[Dict[str, Any]]:
    conn = get_connection(path)
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return user


def get_user_by_id(path: str, user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection(path)
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user


def update_user_totp(path: str, user_id: int, totp_secret: str) -> None:
    conn = get_connection(path)
    with conn:
        conn.execute(
            "UPDATE users SET totp_secret = ? WHERE id = ?",
            (totp_secret, user_id),
        )
    conn.close()


def create_credential(
    path: str,
    user_id: int,
    service: str,
    account: str,
    encrypted_password: str,
    nonce: str,
) -> int:
    conn = get_connection(path)
    with conn:
        cursor = conn.execute(
            "INSERT INTO vault_credentials (user_id, service, account, encrypted_password, nonce) VALUES (?, ?, ?, ?, ?)",
            (user_id, service, account, encrypted_password, nonce),
        )
    conn.close()
    return cursor.lastrowid


def get_credentials_for_user(path: str, user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection(path)
    rows = conn.execute(
        "SELECT * FROM vault_credentials WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return rows


def get_credential_by_id(path: str, credential_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection(path)
    row = conn.execute("SELECT * FROM vault_credentials WHERE id = ?", (credential_id,)).fetchone()
    conn.close()
    return row


def update_credential(
    path: str,
    credential_id: int,
    service: str,
    account: str,
    encrypted_password: str,
    nonce: str,
) -> None:
    conn = get_connection(path)
    with conn:
        conn.execute(
            "UPDATE vault_credentials SET service = ?, account = ?, encrypted_password = ?, nonce = ? WHERE id = ?",
            (service, account, encrypted_password, nonce, credential_id),
        )
    conn.close()


def delete_credential(path: str, credential_id: int) -> None:
    conn = get_connection(path)
    with conn:
        conn.execute("DELETE FROM vault_credentials WHERE id = ?", (credential_id,))
    conn.close()
