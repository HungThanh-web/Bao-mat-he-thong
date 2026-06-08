import base64
import hashlib
import json
import urllib.request
from datetime import datetime, timezone

from flask import (
    Blueprint,
    Response,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from backend.crypto import (
    decrypt_export_payload,
    decrypt_password,
    derive_master_key,
    encrypt_export_payload,
    encrypt_password,
    generate_salt,
    generate_totp_secret,
    get_totp_uri,
    hash_master_password,
    password_strength,
    verify_master_password,
    verify_totp,
)
from backend.db import (
    create_credential,
    create_user,
    delete_credential,
    get_categories_for_user,
    get_credential_by_id,
    get_credentials_for_user,
    get_user_by_id,
    get_user_by_username,
    init_db,
    update_credential,
    update_user_totp,
)

routes = Blueprint("routes", __name__)


def _is_logged_in() -> bool:
    return session.get("user_id") is not None


def _master_key() -> bytes:
    key_b64 = session.get("master_key")
    if not key_b64:
        raise RuntimeError("Không tìm thấy khóa phiên. Vui lòng đăng nhập lại.")
    return base64.b64decode(key_b64)


def _require_vault_access():
    if not _is_logged_in():
        return redirect(url_for("routes.login"))
    user = get_user_by_id(routes.db_path, session["user_id"])
    if not user:
        session.clear()
        return redirect(url_for("routes.login"))
    if user.get("totp_secret") and not session.get("otp_verified"):
        return redirect(url_for("routes.otp"))
    return None


def _credential_plaintext(item: dict) -> str | None:
    try:
        return decrypt_password(item["encrypted_password"], item["nonce"], _master_key())
    except Exception:
        return None


def _password_age_days(item: dict) -> int | None:
    value = item.get("updated_at") or item.get("created_at")
    if not value:
        return None
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                value = datetime.strptime(value, fmt)
                break
            except ValueError:
                continue
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - value.astimezone(timezone.utc)).days


def _build_audit(credentials: list[dict]) -> tuple[list[dict], dict]:
    decrypted = []
    password_seen: dict[str, list[dict]] = {}
    totals = {"weak": 0, "duplicate": 0, "old": 0}

    for item in credentials:
        plaintext = _credential_plaintext(item)
        strength_label, strength_class, details = password_strength(plaintext or "")
        age_days = _password_age_days(item)
        if strength_class == "strength-weak":
            totals["weak"] += 1
        if age_days is not None and age_days >= 180:
            totals["old"] += 1
        if plaintext:
            password_seen.setdefault(plaintext, []).append(item)
        decrypted.append(
            {
                **item,
                "password": plaintext or "[Không giải mã được]",
                "password_strength_label": strength_label,
                "password_strength_class": strength_class,
                "password_age_days": age_days,
                "audit_details": details,
                "is_duplicate": False,
            }
        )

    duplicate_ids = {
        item["id"]
        for group in password_seen.values()
        if len(group) > 1
        for item in group
    }
    totals["duplicate"] = len(duplicate_ids)
    for item in decrypted:
        item["is_duplicate"] = item["id"] in duplicate_ids

    return decrypted, totals


@routes.route("/")
def index():
    if _is_logged_in():
        return redirect(url_for("routes.dashboard"))
    return redirect(url_for("routes.login"))


@routes.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = get_user_by_username(routes.db_path, username)
        if not user:
            flash("Tên đăng nhập không tồn tại.", "error")
            return render_template("login.html")

        salt = base64.b64decode(user["salt"])
        if not verify_master_password(password, salt, user["password_hash"]):
            flash("Sai Master Password.", "error")
            return render_template("login.html")

        master_key = derive_master_key(password, salt)
        session.permanent = True
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["master_key"] = base64.b64encode(master_key).decode("utf-8")
        session["otp_verified"] = False

        if user.get("totp_secret"):
            return redirect(url_for("routes.otp"))
        return redirect(url_for("routes.dashboard"))

    return render_template("login.html")


@routes.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        if not username or not password:
            flash("Vui lòng nhập tên đăng nhập và Master Password.", "error")
            return render_template("register.html")
        if password != confirm:
            flash("Mật khẩu xác nhận không khớp.", "error")
            return render_template("register.html")
        if get_user_by_username(routes.db_path, username):
            flash("Tên đăng nhập đã tồn tại.", "error")
            return render_template("register.html")

        salt = generate_salt()
        hashed = hash_master_password(password, salt)
        create_user(routes.db_path, username, hashed, base64.b64encode(salt).decode("utf-8"))

        flash("Đăng ký thành công. Mời đăng nhập.", "success")
        return redirect(url_for("routes.login"))

    return render_template("register.html")


@routes.route("/otp", methods=["GET", "POST"])
def otp():
    if not _is_logged_in():
        return redirect(url_for("routes.login"))

    user = get_user_by_id(routes.db_path, session["user_id"])
    if not user or not user.get("totp_secret"):
        return redirect(url_for("routes.dashboard"))

    if request.method == "POST":
        token = request.form.get("token", "").strip()
        if verify_totp(user["totp_secret"], token):
            session["otp_verified"] = True
            return redirect(url_for("routes.dashboard"))
        flash("Mã OTP không đúng. Vui lòng thử lại.", "error")

    return render_template("otp.html")


@routes.route("/security/2fa", methods=["GET", "POST"])
def setup_2fa():
    redirect_response = _require_vault_access()
    if redirect_response:
        return redirect_response

    user = get_user_by_id(routes.db_path, session["user_id"])
    if request.method == "POST":
        action = request.form.get("action")
        if action == "disable":
            update_user_totp(routes.db_path, session["user_id"], None)
            session["otp_verified"] = False
            flash("Đã tắt xác thực 2 yếu tố.", "success")
            return redirect(url_for("routes.dashboard"))

        secret = session.get("pending_totp_secret")
        token = request.form.get("token", "").strip()
        if secret and verify_totp(secret, token):
            update_user_totp(routes.db_path, session["user_id"], secret)
            session.pop("pending_totp_secret", None)
            session["otp_verified"] = True
            flash("Đã bật xác thực 2 yếu tố.", "success")
            return redirect(url_for("routes.dashboard"))
        flash("Mã OTP không hợp lệ.", "error")

    if not session.get("pending_totp_secret"):
        session["pending_totp_secret"] = generate_totp_secret()

    secret = session["pending_totp_secret"]
    return render_template(
        "setup_2fa.html",
        enabled=bool(user.get("totp_secret")),
        secret=secret,
        otp_uri=get_totp_uri(session["username"], secret),
    )


@routes.route("/dashboard")
def dashboard():
    redirect_response = _require_vault_access()
    if redirect_response:
        return redirect_response

    query = request.args.get("q", "").strip().lower()
    category = request.args.get("category", "").strip()
    credentials = get_credentials_for_user(routes.db_path, session["user_id"])
    decrypted, audit_totals = _build_audit(credentials)

    if query:
        decrypted = [
            item
            for item in decrypted
            if query in item.get("service", "").lower()
            or query in item.get("account", "").lower()
            or query in (item.get("url") or "").lower()
            or query in (item.get("notes") or "").lower()
        ]
    if category:
        decrypted = [item for item in decrypted if item.get("category") == category]

    return render_template(
        "dashboard.html",
        credentials=decrypted,
        username=session.get("username"),
        query=query,
        selected_category=category,
        categories=get_categories_for_user(routes.db_path, session["user_id"]),
        audit_totals=audit_totals,
    )


@routes.route("/audit")
def audit_all():
    redirect_response = _require_vault_access()
    if redirect_response:
        return redirect_response

    credentials = get_credentials_for_user(routes.db_path, session["user_id"])
    decrypted, audit_totals = _build_audit(credentials)
    return render_template("audit_all.html", credentials=decrypted, audit_totals=audit_totals)


@routes.route("/audit/<int:credential_id>")
def audit_credential(credential_id: int):
    redirect_response = _require_vault_access()
    if redirect_response:
        return redirect_response

    cred = get_credential_by_id(routes.db_path, credential_id)
    if not cred or cred["user_id"] != session["user_id"]:
        flash("Không tìm thấy mục này.", "error")
        return redirect(url_for("routes.dashboard"))

    plaintext = _credential_plaintext(cred)
    strength_label, strength_class, details = password_strength(plaintext or "")
    duplicates = []
    if plaintext:
        all_creds = get_credentials_for_user(routes.db_path, session["user_id"])
        for other in all_creds:
            if other["id"] == credential_id:
                continue
            other_plain = _credential_plaintext(other)
            if other_plain and other_plain == plaintext:
                duplicates.append({"id": other["id"], "service": other["service"], "account": other["account"]})

    return render_template(
        "audit.html",
        credential=cred,
        password=plaintext,
        strength_label=strength_label,
        strength_class=strength_class,
        details=details,
        duplicates=duplicates,
        age_days=_password_age_days(cred),
    )


@routes.route("/breach/<int:credential_id>")
def breach_check(credential_id: int):
    redirect_response = _require_vault_access()
    if redirect_response:
        return redirect_response

    cred = get_credential_by_id(routes.db_path, credential_id)
    if not cred or cred["user_id"] != session["user_id"]:
        flash("Không tìm thấy mục này.", "error")
        return redirect(url_for("routes.dashboard"))

    plaintext = _credential_plaintext(cred)
    if not plaintext:
        flash("Không giải mã được mật khẩu để kiểm tra rò rỉ.", "error")
        return redirect(url_for("routes.audit_credential", credential_id=credential_id))

    sha1 = hashlib.sha1(plaintext.encode("utf-8")).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]
    try:
        req = urllib.request.Request(
            f"https://api.pwnedpasswords.com/range/{prefix}",
            headers={"User-Agent": "MiniPasswordVault"},
        )
        with urllib.request.urlopen(req, timeout=8) as response:
            body = response.read().decode("utf-8")
        found_count = 0
        for line in body.splitlines():
            candidate_suffix, count = line.split(":")
            if candidate_suffix == suffix:
                found_count = int(count)
                break
        if found_count:
            flash(f"Mật khẩu này đã xuất hiện trong {found_count:,} bản ghi rò rỉ. Hãy đổi ngay.", "error")
        else:
            flash("Chưa tìm thấy mật khẩu này trong dữ liệu rò rỉ của HIBP.", "success")
    except Exception:
        flash("Không thể kiểm tra rò rỉ lúc này. Vui lòng thử lại sau.", "error")
    return redirect(url_for("routes.audit_credential", credential_id=credential_id))


@routes.route("/add", methods=["GET", "POST"])
def add_credential_route():
    redirect_response = _require_vault_access()
    if redirect_response:
        return redirect_response

    if request.method == "POST":
        service = request.form.get("service", "").strip()
        account = request.form.get("account", "").strip()
        url = request.form.get("url", "").strip()
        notes = request.form.get("notes", "").strip()
        category = request.form.get("category", "").strip() or "Cá nhân"
        password = request.form.get("password", "")

        if not service or not account or not password:
            flash("Vui lòng nhập đầy đủ dịch vụ, tài khoản và mật khẩu.", "error")
            return render_template("add_edit.html")

        encrypted_password, nonce = encrypt_password(password, _master_key())
        create_credential(routes.db_path, session["user_id"], service, account, url, notes, category, encrypted_password, nonce)
        flash("Lưu thông tin thành công.", "success")
        return redirect(url_for("routes.dashboard"))

    return render_template("add_edit.html")


@routes.route("/edit/<int:credential_id>", methods=["GET", "POST"])
def edit_credential_route(credential_id: int):
    redirect_response = _require_vault_access()
    if redirect_response:
        return redirect_response

    credential = get_credential_by_id(routes.db_path, credential_id)
    if not credential or credential["user_id"] != session["user_id"]:
        flash("Không tìm thấy mục này.", "error")
        return redirect(url_for("routes.dashboard"))

    if request.method == "POST":
        service = request.form.get("service", "").strip()
        account = request.form.get("account", "").strip()
        url = request.form.get("url", "").strip()
        notes = request.form.get("notes", "").strip()
        category = request.form.get("category", "").strip() or "Cá nhân"
        password = request.form.get("password", "")

        if not service or not account or not password:
            flash("Vui lòng nhập đầy đủ dịch vụ, tài khoản và mật khẩu.", "error")
            return render_template("add_edit.html", credential=credential)

        encrypted_password, nonce = encrypt_password(password, _master_key())
        update_credential(routes.db_path, credential_id, service, account, url, notes, category, encrypted_password, nonce)
        flash("Cập nhật thành công.", "success")
        return redirect(url_for("routes.dashboard"))

    credential = {**credential, "password": _credential_plaintext(credential) or ""}
    return render_template("add_edit.html", credential=credential)


@routes.route("/delete/<int:credential_id>", methods=["POST"])
def delete_credential_route(credential_id: int):
    redirect_response = _require_vault_access()
    if redirect_response:
        return redirect_response

    credential = get_credential_by_id(routes.db_path, credential_id)
    if credential and credential["user_id"] == session["user_id"]:
        delete_credential(routes.db_path, credential_id)
        flash("Đã xóa mật khẩu.", "success")
    else:
        flash("Không tìm thấy mục để xóa.", "error")
    return redirect(url_for("routes.dashboard"))


@routes.route("/export", methods=["GET", "POST"])
def export_vault():
    redirect_response = _require_vault_access()
    if redirect_response:
        return redirect_response

    if request.method == "POST":
        passphrase = request.form.get("passphrase", "")
        if len(passphrase) < 8:
            flash("Mật khẩu export cần tối thiểu 8 ký tự.", "error")
            return render_template("import_export.html", mode="export")

        credentials = get_credentials_for_user(routes.db_path, session["user_id"])
        payload = {
            "app": "MiniPasswordVault",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "items": [
                {
                    "service": item["service"],
                    "account": item["account"],
                    "url": item.get("url") or "",
                    "notes": item.get("notes") or "",
                    "category": item.get("category") or "Cá nhân",
                    "password": _credential_plaintext(item) or "",
                }
                for item in credentials
            ],
        }
        envelope = encrypt_export_payload(payload, passphrase)
        body = json.dumps(envelope, ensure_ascii=False, indent=2)
        return Response(
            body,
            mimetype="application/json",
            headers={"Content-Disposition": "attachment; filename=mini-password-vault.enc.json"},
        )

    return render_template("import_export.html", mode="export")


@routes.route("/import", methods=["GET", "POST"])
def import_vault():
    redirect_response = _require_vault_access()
    if redirect_response:
        return redirect_response

    if request.method == "POST":
        passphrase = request.form.get("passphrase", "")
        upload = request.files.get("vault_file")
        if not upload or not passphrase:
            flash("Vui lòng chọn file và nhập mật khẩu import.", "error")
            return render_template("import_export.html", mode="import")

        try:
            envelope = json.loads(upload.read().decode("utf-8"))
            payload = decrypt_export_payload(envelope, passphrase)
            imported = 0
            for item in payload.get("items", []):
                password = item.get("password") or ""
                service = item.get("service") or ""
                account = item.get("account") or ""
                if not service or not account or not password:
                    continue
                encrypted_password, nonce = encrypt_password(password, _master_key())
                create_credential(
                    routes.db_path,
                    session["user_id"],
                    service,
                    account,
                    item.get("url") or "",
                    item.get("notes") or "",
                    item.get("category") or "Cá nhân",
                    encrypted_password,
                    nonce,
                )
                imported += 1
            flash(f"Đã nhập {imported} mục vào kho mật khẩu.", "success")
            return redirect(url_for("routes.dashboard"))
        except Exception:
            flash("Không thể giải mã hoặc đọc file import.", "error")

    return render_template("import_export.html", mode="import")


@routes.route("/logout")
def logout():
    session.clear()
    flash("Bạn đã đăng xuất.", "success")
    return redirect(url_for("routes.login"))


def register_routes(app, db_path: str):
    routes.db_path = db_path
    app.register_blueprint(routes)
    init_db(db_path)
