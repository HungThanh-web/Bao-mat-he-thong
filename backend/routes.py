import base64

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from backend.crypto import (
    derive_master_key,
    encrypt_password,
    generate_salt,
    password_strength,
    hash_master_password,
    verify_master_password,
    verify_totp,
)
from backend.db import (
    create_credential,
    create_user,
    delete_credential,
    get_credential_by_id,
    get_credentials_for_user,
    get_user_by_id,
    get_user_by_username,
    init_db,
    update_credential,
)

routes = Blueprint("routes", __name__)


def _is_logged_in() -> bool:
    return session.get("user_id") is not None


def _master_key() -> bytes:
    key_b64 = session.get("master_key")
    if not key_b64:
        raise RuntimeError("Master key is not available in session")
    return base64.b64decode(key_b64)


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
            flash("Sai mật khẩu chính.", "error")
            return render_template("login.html")

        master_key = derive_master_key(password, salt)
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
            flash("Vui lòng nhập tên đăng nhập và mật khẩu.", "error")
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


@routes.route("/dashboard")
def dashboard():
    if not _is_logged_in():
        return redirect(url_for("routes.login"))

    user = get_user_by_id(routes.db_path, session["user_id"])
    if user.get("totp_secret") and not session.get("otp_verified"):
        return redirect(url_for("routes.otp"))

    credentials = get_credentials_for_user(routes.db_path, session["user_id"])
    decrypted = []
    master_key = _master_key()
    for item in credentials:
        plaintext = None
        strength_label = ""
        strength_class = "strength-neutral"
        try:
            from backend.crypto import decrypt_password

            plaintext = decrypt_password(item["encrypted_password"], item["nonce"], master_key)
            if plaintext:
                strength_label, strength_class, _ = password_strength(plaintext)
            else:
                strength_label = "Không giải mã được"
                strength_class = "strength-weak"
        except Exception:
            plaintext = "[Không giải mã được]"
            strength_label = "Không giải mã được"
            strength_class = "strength-weak"
        decrypted.append({
            **item,
            "password": plaintext or "[Lỗi giải mã]",
            "password_strength_label": strength_label,
            "password_strength_class": strength_class,
        })

    return render_template("dashboard.html", credentials=decrypted, username=session.get("username"))


@routes.route("/audit/<int:credential_id>")
def audit_credential(credential_id: int):
    if not _is_logged_in():
        return redirect(url_for("routes.login"))

    cred = get_credential_by_id(routes.db_path, credential_id)
    if not cred or cred["user_id"] != session["user_id"]:
        flash("Không tìm thấy mục này.", "error")
        return redirect(url_for("routes.dashboard"))

    master_key = _master_key()
    try:
        from backend.crypto import decrypt_password

        plaintext = decrypt_password(cred["encrypted_password"], cred["nonce"], master_key)
    except Exception:
        plaintext = None

    strength_label, strength_class, details = (None, None, {})
    duplicates = []
    if plaintext:
        strength_label, strength_class, details = password_strength(plaintext)
        # detect duplicates in user's vault
        all_creds = get_credentials_for_user(routes.db_path, session["user_id"])
        for other in all_creds:
            if other["id"] == credential_id:
                continue
            try:
                other_plain = decrypt_password(other["encrypted_password"], other["nonce"], master_key)
                if other_plain and other_plain == plaintext:
                    duplicates.append({"id": other["id"], "service": other["service"], "account": other["account"]})
            except Exception:
                pass

    return render_template("audit.html", credential=cred, password=plaintext, strength_label=strength_label, strength_class=strength_class, details=details, duplicates=duplicates)


@routes.route("/add", methods=["GET", "POST"])
def add_credential_route():
    if not _is_logged_in():
        return redirect(url_for("routes.login"))

    if request.method == "POST":
        service = request.form.get("service", "").strip()
        account = request.form.get("account", "").strip()
        password = request.form.get("password", "")

        if not service or not account or not password:
            flash("Vui lòng nhập đầy đủ thông tin.", "error")
            return render_template("add_edit.html")

        encrypted_password, nonce = encrypt_password(password, _master_key())
        create_credential(routes.db_path, session["user_id"], service, account, encrypted_password, nonce)
        flash("Lưu thông tin thành công.", "success")
        return redirect(url_for("routes.dashboard"))

    return render_template("add_edit.html")


@routes.route("/edit/<int:credential_id>", methods=["GET", "POST"])
def edit_credential_route(credential_id: int):
    if not _is_logged_in():
        return redirect(url_for("routes.login"))

    credential = get_credential_by_id(routes.db_path, credential_id)
    if not credential or credential["user_id"] != session["user_id"]:
        flash("Không tìm thấy mục này.", "error")
        return redirect(url_for("routes.dashboard"))

    if request.method == "POST":
        service = request.form.get("service", "").strip()
        account = request.form.get("account", "").strip()
        password = request.form.get("password", "")

        if not service or not account or not password:
            flash("Vui lòng nhập đầy đủ thông tin.", "error")
            return render_template("add_edit.html", credential=credential)

        encrypted_password, nonce = encrypt_password(password, _master_key())
        update_credential(routes.db_path, credential_id, service, account, encrypted_password, nonce)
        flash("Cập nhật thành công.", "success")
        return redirect(url_for("routes.dashboard"))

    return render_template("add_edit.html", credential=credential)


@routes.route("/delete/<int:credential_id>", methods=["POST"])
def delete_credential_route(credential_id: int):
    if not _is_logged_in():
        return redirect(url_for("routes.login"))

    credential = get_credential_by_id(routes.db_path, credential_id)
    if credential and credential["user_id"] == session["user_id"]:
        delete_credential(routes.db_path, credential_id)
        flash("Đã xóa mật khẩu.", "success")
    else:
        flash("Không tìm thấy mục để xóa.", "error")
    return redirect(url_for("routes.dashboard"))


@routes.route("/logout")
def logout():
    session.clear()
    flash("Bạn đã đăng xuất.", "success")
    return redirect(url_for("routes.login"))


def register_routes(app, db_path: str):
    routes.db_path = db_path
    app.register_blueprint(routes)
    init_db(db_path)
