import json
import os
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, current_app
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Backup, AuditLog, BusinessSettings, User
from app.backup_engine import dump_all, restore_all, reset_business_data

backup_bp = Blueprint("backup", __name__, url_prefix="/backup")


def _backups_dir():
    path = os.path.join(current_app.root_path, "..", "backups")
    path = os.path.abspath(path)
    os.makedirs(path, exist_ok=True)
    return path


@backup_bp.route("/")
@login_required
def index():
    history = Backup.query.order_by(Backup.created_at.desc()).all()
    business = BusinessSettings.query.get("singleton")
    return render_template("backup/index.html", history=history, business_name=business.business_name if business else "")


@backup_bp.route("/create", methods=["POST"])
@login_required
def create_backup():
    data = dump_all()
    payload = json.dumps({"created_at": datetime.utcnow().isoformat(), "data": data}, indent=2)

    filename = f"backup-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.json"
    filepath = os.path.join(_backups_dir(), filename)
    with open(filepath, "w") as f:
        f.write(payload)

    size_bytes = os.path.getsize(filepath)

    backup = Backup(filename=filename, size_bytes=size_bytes, created_by_id=current_user.id)
    db.session.add(backup)
    db.session.add(AuditLog(user_id=current_user.id, action="CREATE", record_type="Backup", record_id=backup.id))
    db.session.commit()

    flash(f"Backup created ({size_bytes:,} bytes).", "success")
    return redirect(url_for("backup.index"))


@backup_bp.route("/<backup_id>/download")
@login_required
def download_backup(backup_id):
    backup = Backup.query.get_or_404(backup_id)
    return send_from_directory(_backups_dir(), backup.filename, as_attachment=True, download_name=backup.filename)


@backup_bp.route("/restore", methods=["POST"])
@login_required
def restore_backup():
    confirm = request.form.get("confirm", "")
    if confirm != "RESTORE":
        flash('Type RESTORE exactly to confirm — nothing was changed.', "error")
        return redirect(url_for("backup.index"))

    file = request.files.get("backup_file")
    if not file or not file.filename:
        flash("Choose a backup file to restore.", "error")
        return redirect(url_for("backup.index"))

    try:
        payload = json.loads(file.read())
        data = payload.get("data", payload)  # tolerate a raw {table: rows} file too
    except (json.JSONDecodeError, UnicodeDecodeError):
        flash("That file isn't a valid backup — it couldn't be read as JSON.", "error")
        return redirect(url_for("backup.index"))

    try:
        restore_all(data)
        db.session.add(AuditLog(user_id=current_user.id, action="UPDATE", record_type="Restore", record_id=None))
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f"Restore failed and no changes were made: {e}", "error")
        return redirect(url_for("backup.index"))

    flash("Backup restored successfully. All data has been replaced with the backup's contents.", "success")
    return redirect(url_for("backup.index"))


@backup_bp.route("/reset", methods=["POST"])
@login_required
def reset():
    business = BusinessSettings.query.get("singleton")
    expected = (business.business_name if business else "").strip()
    confirm = request.form.get("confirm", "").strip()

    if not expected or confirm != expected:
        flash(f'Type the business name exactly ("{expected}") to confirm — nothing was deleted.', "error")
        return redirect(url_for("backup.index"))

    try:
        reset_business_data()
        db.session.add(AuditLog(user_id=current_user.id, action="DELETE", record_type="DangerZoneReset", record_id=None))
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f"Reset failed and no changes were made: {e}", "error")
        return redirect(url_for("backup.index"))

    flash("All business data has been permanently deleted. Your login and settings were kept.", "success")
    return redirect(url_for("backup.index"))
