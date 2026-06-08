import os
from typing import Any, Dict, List, Optional

import pymysql
from pymysql.cursors import DictCursor


DB_SCHEMA_MYSQL = [
    "CREATE TABLE IF NOT EXISTS users ("
    "id INT AUTO_INCREMENT PRIMARY KEY, "
    "username VARCHAR(255) UNIQUE NOT NULL, "
    "password_hash TEXT NOT NULL, "
    "salt TEXT NOT NULL, "
    "totp_secret TEXT"
    ") ENGINE=InnoDB",
    "CREATE TABLE IF NOT EXISTS vault_credentials ("
    "id INT AUTO_INCREMENT PRIMARY KEY, "
    "user_id INT NOT NULL, "
    "service VARCHAR(255) NOT NULL, "
    "account VARCHAR(255) NOT NULL, "
    "url TEXT, "
    "notes TEXT, "
    "category VARCHAR(120) DEFAULT 'Cá nhân', "
    "encrypted_password TEXT NOT NULL, "
    "nonce TEXT NOT NULL, "
    "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
    "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, "
    "FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE"
    ") ENGINE=InnoDB",
]

VAULT_COLUMN_MIGRATIONS = {
    "url": "ALTER TABLE vault_credentials ADD COLUMN url TEXT",
    "notes": "ALTER TABLE vault_credentials ADD COLUMN notes TEXT",
    "category": "ALTER TABLE vault_credentials ADD COLUMN category VARCHAR(120) DEFAULT 'Cá nhân'",
    "updated_at": (
        "ALTER TABLE vault_credentials ADD COLUMN updated_at "
        "TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
    ),
}


def get_connection(path: str):
    """Connect to Aiven MySQL using environment variables.
    
    Requires: DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
    """
    if pymysql is None:
        raise RuntimeError("PyMySQL is required. Install with 'pip install PyMySQL'.")
    
    conn_args = {
        "host": os.environ.get("DB_HOST"),
        "port": int(os.environ.get("DB_PORT", 20380)),
        "user": os.environ.get("DB_USER"),
        "password": os.environ.get("DB_PASSWORD"),
        "database": os.environ.get("DB_NAME", "defaultdb"),
        "cursorclass": DictCursor,
    }
    
    # Add SSL CA if provided
    ca_path = os.environ.get("MYSQL_SSL_CA")
    if ca_path:
        conn_args["ssl"] = {"ca": ca_path}
    
    conn = pymysql.connect(**conn_args)
    return conn


def init_db(path: str) -> None:
    """Initialize MySQL database schema."""
    conn = get_connection(path)
    try:
        with conn.cursor() as cur:
            for stmt in DB_SCHEMA_MYSQL:
                cur.execute(stmt)
            cur.execute("SHOW COLUMNS FROM vault_credentials")
            existing_columns = {row["Field"] for row in cur.fetchall()}
            for column, stmt in VAULT_COLUMN_MIGRATIONS.items():
                if column not in existing_columns:
                    cur.execute(stmt)
        conn.commit()
    finally:
        conn.close()


def create_user(path: str, username: str, password_hash: str, salt: str, totp_secret: Optional[str] = None) -> int:
    conn = get_connection(path)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (username, password_hash, salt, totp_secret) VALUES (%s, %s, %s, %s)",
                (username, password_hash, salt, totp_secret),
            )
            conn.commit()
            return cur.lastrowid
    finally:
        conn.close()


def get_user_by_username(path: str, username: str) -> Optional[Dict[str, Any]]:
    conn = get_connection(path)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            return cur.fetchone()
    finally:
        conn.close()


def get_user_by_id(path: str, user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection(path)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            return cur.fetchone()
    finally:
        conn.close()


def update_user_totp(path: str, user_id: int, totp_secret: Optional[str]) -> None:
    conn = get_connection(path)
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET totp_secret = %s WHERE id = %s", (totp_secret, user_id))
            conn.commit()
    finally:
        conn.close()


def create_credential(
    path: str,
    user_id: int,
    service: str,
    account: str,
    url: str,
    notes: str,
    category: str,
    encrypted_password: str,
    nonce: str,
) -> int:
    conn = get_connection(path)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO vault_credentials "
                "(user_id, service, account, url, notes, category, encrypted_password, nonce) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (user_id, service, account, url, notes, category, encrypted_password, nonce),
            )
            conn.commit()
            return cur.lastrowid
    finally:
        conn.close()


def get_credentials_for_user(path: str, user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection(path)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM vault_credentials WHERE user_id = %s ORDER BY created_at DESC",
                (user_id,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def get_categories_for_user(path: str, user_id: int) -> List[str]:
    conn = get_connection(path)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT DISTINCT category FROM vault_credentials "
                "WHERE user_id = %s AND category IS NOT NULL AND category <> '' "
                "ORDER BY category",
                (user_id,),
            )
            return [row["category"] for row in cur.fetchall()]
    finally:
        conn.close()


def get_credential_by_id(path: str, credential_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection(path)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM vault_credentials WHERE id = %s", (credential_id,))
            return cur.fetchone()
    finally:
        conn.close()


def update_credential(
    path: str,
    credential_id: int,
    service: str,
    account: str,
    url: str,
    notes: str,
    category: str,
    encrypted_password: str,
    nonce: str,
) -> None:
    conn = get_connection(path)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE vault_credentials SET service = %s, account = %s, url = %s, "
                "notes = %s, category = %s, encrypted_password = %s, nonce = %s "
                "WHERE id = %s",
                (service, account, url, notes, category, encrypted_password, nonce, credential_id),
            )
            conn.commit()
    finally:
        conn.close()


def delete_credential(path: str, credential_id: int) -> None:
    conn = get_connection(path)
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM vault_credentials WHERE id = %s", (credential_id,))
            conn.commit()
    finally:
        conn.close()
