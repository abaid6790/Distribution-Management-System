from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models import AuditLog

account_bp = Blueprint("account", __name__, url_prefix="/account")


@account_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    forced = current_user.must_change_password

    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        errors = []
        if not check_password_hash(current_user.password_hash, current_password):
            errors.append("Current password is incorrect.")
        if len(new_password) < 8:
            errors.append("New password must be at least 8 characters.")
        if new_password != confirm_password:
            errors.append("New password and confirmation don't match.")
        if new_password and check_password_hash(current_user.password_hash, new_password):
            errors.append("New password must be different from your current password.")

        if errors:
            return render_template("account/change_password.html", errors=errors, forced=forced)

        current_user.password_hash = generate_password_hash(new_password)
        current_user.must_change_password = False
        db.session.add(
            AuditLog(user_id=current_user.id, action="UPDATE", record_type="User", record_id=current_user.id, new_value={"action": "password_changed"})
        )
        db.session.commit()

        flash("Password updated.", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("account/change_password.html", errors=[], forced=forced)
