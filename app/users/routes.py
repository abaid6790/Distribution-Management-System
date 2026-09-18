import secrets
import string

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import User, Employee, AuditLog
from app.permissions import PERMISSION_MODULES, admin_required

users_bp = Blueprint("users", __name__, url_prefix="/users")

ROLES = ["ADMIN", "MANAGER", "SALESMAN", "ACCOUNTANT"]

# Sensible starting checkbox state per role — the admin can still change
# every box afterward. Picking a role just pre-fills a reasonable default.
ROLE_DEFAULT_PERMISSIONS = {
    "ADMIN": [k for k, _, _ in PERMISSION_MODULES],
    "MANAGER": [k for k, _, _ in PERMISSION_MODULES if k not in ("backup",)],
    "ACCOUNTANT": ["debtors", "creditors", "transactions", "expenses", "reports", "invoices", "customers", "suppliers"],
    "SALESMAN": ["sales", "sale_returns", "customers", "load_card"],
}


def _generate_password(length=10):
    alphabet = string.ascii_letters + string.digits
    # Guarantee at least one digit and one letter for readability/acceptance.
    while True:
        pwd = "".join(secrets.choice(alphabet) for _ in range(length))
        if any(c.isdigit() for c in pwd) and any(c.isalpha() for c in pwd):
            return pwd


def _grouped_modules():
    groups = {}
    for key, label, group in PERMISSION_MODULES:
        groups.setdefault(group, []).append((key, label))
    return groups


def _active_admin_count(exclude_user_id=None):
    q = User.query.filter_by(role="ADMIN", is_active=True)
    if exclude_user_id:
        q = q.filter(User.id != exclude_user_id)
    return q.count()


@users_bp.route("/")
@login_required
@admin_required
def list_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("users/list.html", users=users)


@users_bp.route("/new", methods=["GET", "POST"])
@login_required
@admin_required
def new_user():
    # Employees who don't already have a login account.
    available_employees = Employee.query.filter_by(is_active=True).filter(
        ~Employee.id.in_(db.session.query(User.employee_id).filter(User.employee_id.isnot(None)))
    ).order_by(Employee.name).all()

    if request.method == "POST":
        errors = []
        employee_mode = request.form.get("employee_mode", "existing")
        employee_id = request.form.get("employee_id", "")
        new_name = request.form.get("new_employee_name", "").strip()
        new_phone = request.form.get("new_employee_phone", "").strip()
        new_email = request.form.get("new_employee_email", "").strip()

        username = request.form.get("username", "").strip().lower()
        role = request.form.get("role", "SALESMAN")
        permissions = request.form.getlist("permissions")

        if role not in ROLES:
            errors.append("Select a valid role.")
        if not username:
            errors.append("Username is required.")
        elif User.query.filter_by(username=username).first():
            errors.append(f'Username "{username}" is already taken.')

        employee = None
        if employee_mode == "existing":
            if not employee_id:
                errors.append("Select an employee.")
            else:
                employee = Employee.query.get(employee_id)
                if not employee:
                    errors.append("Selected employee no longer exists.")
        else:
            if not new_name:
                errors.append("Employee name is required.")

        if errors:
            groups = _grouped_modules()
            return render_template(
                "users/form.html",
                user=None,
                roles=ROLES,
                groups=groups,
                role_defaults=ROLE_DEFAULT_PERMISSIONS,
                available_employees=available_employees,
                errors=errors,
                form=request.form,
            )

        if employee_mode == "new":
            last = Employee.query.order_by(Employee.created_at.desc()).first()
            import re

            m = re.search(r"(\d+)$", last.employee_code) if last and last.employee_code else None
            next_num = int(m.group(1)) + 1 if m else 1
            employee = Employee(
                employee_code=f"EMP-{str(next_num).zfill(4)}",
                name=new_name,
                phone=new_phone or None,
                email=new_email or None,
            )
            db.session.add(employee)
            db.session.flush()

        password = _generate_password()
        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            full_name=employee.name,
            role=role,
            permissions=permissions if role != "ADMIN" else [],
            must_change_password=True,
            employee_id=employee.id,
        )
        db.session.add(user)
        db.session.flush()

        db.session.add(AuditLog(user_id=current_user.id, action="CREATE", record_type="User", record_id=user.id))
        db.session.commit()

        return render_template("users/created.html", user=user, password=password)

    groups = _grouped_modules()
    return render_template(
        "users/form.html",
        user=None,
        roles=ROLES,
        groups=groups,
        role_defaults=ROLE_DEFAULT_PERMISSIONS,
        available_employees=available_employees,
        errors=[],
        form={},
    )


@users_bp.route("/<user_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == "POST":
        errors = []
        role = request.form.get("role", user.role)
        permissions = request.form.getlist("permissions")
        is_active = request.form.get("is_active") == "on"

        if role not in ROLES:
            errors.append("Select a valid role.")

        # Never allow the last active admin to be demoted or deactivated —
        # that would lock everyone out of user management permanently.
        was_admin = user.role == "ADMIN" and user.is_active
        becoming_non_admin_or_inactive = (role != "ADMIN") or not is_active
        if was_admin and becoming_non_admin_or_inactive and _active_admin_count(exclude_user_id=user.id) == 0:
            errors.append("You can't remove the last active administrator.")

        if errors:
            groups = _grouped_modules()
            return render_template(
                "users/form.html", user=user, roles=ROLES, groups=groups, role_defaults=ROLE_DEFAULT_PERMISSIONS,
                available_employees=[], errors=errors, form=request.form,
            )

        user.role = role
        user.permissions = permissions if role != "ADMIN" else []
        user.is_active = is_active
        db.session.add(AuditLog(user_id=current_user.id, action="UPDATE", record_type="User", record_id=user.id))
        db.session.commit()

        flash(f"{user.full_name}'s access has been updated.", "success")
        return redirect(url_for("users.list_users"))

    groups = _grouped_modules()
    form = {"role": user.role, "permissions": user.permissions or [], "is_active": user.is_active}
    return render_template(
        "users/form.html", user=user, roles=ROLES, groups=groups, role_defaults=ROLE_DEFAULT_PERMISSIONS,
        available_employees=[], errors=[], form=form,
    )


@users_bp.route("/<user_id>/reset-password", methods=["POST"])
@login_required
@admin_required
def reset_password(user_id):
    user = User.query.get_or_404(user_id)
    password = _generate_password()
    user.password_hash = generate_password_hash(password)
    user.must_change_password = True
    db.session.add(AuditLog(user_id=current_user.id, action="UPDATE", record_type="User", record_id=user.id, new_value={"action": "password_reset"}))
    db.session.commit()

    return render_template("users/created.html", user=user, password=password, is_reset=True)
