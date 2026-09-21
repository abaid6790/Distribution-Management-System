from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash

from app.extensions import db, limiter
from app.models import User, AuditLog

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        next_url = request.form.get("next") or url_for("main.dashboard")

        error = None
        if not username or not password:
            error = "Enter your username and password."
        else:
            user = User.query.filter_by(username=username).first()
            if not user or not user.is_active or not check_password_hash(user.password_hash, password):
                error = "That username and password don't match our records."

        if error:
            return render_template("auth/login.html", error=error, next=next_url)

        login_user(user)
        db.session.add(
            AuditLog(user_id=user.id, action="LOGIN", record_type="User", record_id=user.id)
        )
        db.session.commit()
        return redirect(next_url if next_url.startswith("/") else url_for("main.dashboard"))

    next_url = request.args.get("next", url_for("main.dashboard"))
    return render_template("auth/login.html", error=None, next=next_url)


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
