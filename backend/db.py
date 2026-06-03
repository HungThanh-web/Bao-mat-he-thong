import sqlite3
import urllib.parse
from typing import Any, Dict, List, Optional

try:
    import pymysql
    from pymysql.cursors import DictCursor
except Exception:  # pragma: no cover - optional dependency
    pymysql = None


DB_SCHEMA_SQLITE = [
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
    "encrypted_password TEXT NOT NULL, "
    "nonce TEXT NOT NULL, "
    "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
    "FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE"
    ") ENGINE=InnoDB",
]


def _dict_factory(cursor: sqlite3.Cursor, row: sqlite3.Row) -> Dict[str, Any]:
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def _is_mysql_url(path: str) -> bool:
    return path.startswith("mysql://") or path.startswith("mysql+" )


def _parse_mysql_url(url: str) -> Dict[str, Any]:
    # Example: mysql://user:pass@host:port/dbname?ssl-mode=REQUIRED
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)
    ssl_mode = query.get("ssl-mode", [None])[0]
    return {
        "host": parsed.hostname,
        "port": parsed.port or 3306,
        "user": urllib.parse.unquote(parsed.username) if parsed.username else None,
        "password": urllib.parse.unquote(parsed.password) if parsed.password else None,
        "db": parsed.path.lstrip("/") if parsed.path else None,
        "ssl_mode": ssl_mode,
    }


def get_connection(path: str):
    """Return a DB connection. For SQLite this is sqlite3.Connection.
    For MySQL this returns a pymysql connection (if pymysql installed).
    """
    if _is_mysql_url(path):
        if pymysql is None:
            raise RuntimeError("PyMySQL is required to connect to MySQL. Install with 'pip install PyMySQL'.")
        cfg = _parse_mysql_url(path)
        conn_args = {
            "host": cfg["host"],
            "user": cfg["user"],
            "password": cfg["password"],
            "port": cfg["port"],
            "database": cfg["db"],
            "cursorclass": DictCursor,
        }
        # SSL handling: user can extend this if they have CA file
        if cfg.get("ssl_mode") and cfg["ssl_mode"].upper() == "REQUIRED":
            conn_args["ssl"] = {}
        conn = pymysql.connect(**conn_args)
        return conn

    # fallback to sqlite
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = _dict_factory
    return conn


def init_db(path: str) -> None:
    conn = get_connection(path)
    try:
        if _is_mysql_url(path):
            with conn.cursor() as cur:
                for stmt in DB_SCHEMA_MYSQL:
                    cur.execute(stmt)
            conn.commit()
        else:
            with conn:
                for statement in DB_SCHEMA_SQLITE:
                    conn.execute(statement)
    finally:
        conn.close()


def create_user(path: str, username: str, password_hash: str, salt: str, totp_secret: Optional[str] = None) -> int:
    conn = get_connection(path)
    try:
        if _is_mysql_url(path):
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (username, password_hash, salt, totp_secret) VALUES (%s, %s, %s, %s)",
                    (username, password_hash, salt, totp_secret),
                )
                conn.commit()
                return cur.lastrowid
        else:
            with conn:
                cursor = conn.execute(
                    "INSERT INTO users (username, password_hash, salt, totp_secret) VALUES (?, ?, ?, ?)",
                    (username, password_hash, salt, totp_secret),
                )
            return cursor.lastrowid
    finally:
        conn.close()


def get_user_by_username(path: str, username: str) -> Optional[Dict[str, Any]]:
    conn = get_connection(path)
    try:
        if _is_mysql_url(path):
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE username = %s", (username,))
                return cur.fetchone()
        else:
            user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            return user
    finally:
        conn.close()


def get_user_by_id(path: str, user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection(path)
    try:
        if _is_mysql_url(path):
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                return cur.fetchone()
        else:
            user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return user
    finally:
        conn.close()


def update_user_totp(path: str, user_id: int, totp_secret: str) -> None:
    conn = get_connection(path)
    try:
        if _is_mysql_url(path):
            with conn.cursor() as cur:
                cur.execute("UPDATE users SET totp_secret = %s WHERE id = %s", (totp_secret, user_id))
                conn.commit()
        else:
            with conn:
                conn.execute(
                    "UPDATE users SET totp_secret = ? WHERE id = ?",
                    (totp_secret, user_id),
                )
    finally:
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
    try:
        if _is_mysql_url(path):
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO vault_credentials (user_id, service, account, encrypted_password, nonce) VALUES (%s, %s, %s, %s, %s)",
                    (user_id, service, account, encrypted_password, nonce),
                )
                conn.commit()
                return cur.lastrowid
        else:
            with conn:
                cursor = conn.execute(
                    "INSERT INTO vault_credentials (user_id, service, account, encrypted_password, nonce) VALUES (?, ?, ?, ?, ?)",
                    (user_id, service, account, encrypted_password, nonce),
                )
            return cursor.lastrowid
    finally:
        conn.close()


def get_credentials_for_user(path: str, user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection(path)
    try:
        if _is_mysql_url(path):
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM vault_credentials WHERE user_id = %s ORDER BY created_at DESC",
                    (user_id,),
                )
                return cur.fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM vault_credentials WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
            return rows
    finally:
        conn.close()


def get_credential_by_id(path: str, credential_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection(path)
    try:
        if _is_mysql_url(path):
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM vault_credentials WHERE id = %s", (credential_id,))
                return cur.fetchone()
        else:
            row = conn.execute("SELECT * FROM vault_credentials WHERE id = ?", (credential_id,)).fetchone()
            return row
    finally:
        conn.close()


def update_credential(
    path: str,
    credential_id: int,
    service: str,
    account: str,
    encrypted_password: str,
    nonce: str,
) -> None:
    conn = get_connection(path)
    try:
        if _is_mysql_url(path):
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE vault_credentials SET service = %s, account = %s, encrypted_password = %s, nonce = %s WHERE id = %s",
                    (service, account, encrypted_password, nonce, credential_id),
                )
                conn.commit()
        else:
            with conn:
                conn.execute(
                    "UPDATE vault_credentials SET service = ?, account = ?, encrypted_password = ?, nonce = ? WHERE id = ?",
                    (service, account, encrypted_password, nonce, credential_id),
                )
    finally:
        conn.close()


def delete_credential(path: str, credential_id: int) -> None:
    conn = get_connection(path)
    try:
        if _is_mysql_url(path):
            with conn.cursor() as cur:
                cur.execute("DELETE FROM vault_credentials WHERE id = %s", (credential_id,))
                conn.commit()
        else:
            with conn:
                conn.execute("DELETE FROM vault_credentials WHERE id = ?", (credential_id,))
    finally:
        conn.close()
