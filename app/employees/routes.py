from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import or_

from app.extensions import db
from app.models import Employee, User, AuditLog

employees_bp = Blueprint("employees", __name__, url_prefix="/employees")


def _next_employee_code():
    last = Employee.query.order_by(Employee.created_at.desc()).first()
    if last and last.employee_code:
        import re

        m = re.search(r"(\d+)$", last.employee_code)
        next_num = int(m.group(1)) + 1 if m else 1
    else:
        next_num = 1
    return f"EMP-{str(next_num).zfill(4)}"


def _validate(form):
    errors = []
    name = form.get("name", "").strip()
    phone = form.get("phone", "").strip()
    address = form.get("address", "").strip()
    cnic = form.get("cnic", "").strip()
    email = form.get("email", "").strip()
    is_active = form.get("is_active") == "on"

    if not name:
        errors.append("Employee name is required.")

    return errors, {
        "name": name,
        "phone": phone or None,
        "address": address or None,
        "cnic": cnic or None,
        "email": email or None,
        "is_active": is_active,
    }


@employees_bp.route("/")
@login_required
def list_employees():
    q = request.args.get("q", "").strip()
    query = Employee.query
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Employee.name.ilike(like), Employee.employee_code.ilike(like), Employee.phone.ilike(like)))
    employees = query.order_by(Employee.name).all()
    return render_template("employees/list.html", employees=employees, q=q)


@employees_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_employee():
    if request.method == "POST":
        errors, data = _validate(request.form)
        if errors:
            return render_template("employees/form.html", employee=None, form=data, errors=errors)

        employee = Employee(employee_code=_next_employee_code(), **data)
        db.session.add(employee)
        db.session.flush()
        db.session.add(AuditLog(user_id=current_user.id, action="CREATE", record_type="Employee", record_id=employee.id))
        db.session.commit()
        flash("Employee added.", "success")
        return redirect(url_for("employees.list_employees"))

    return render_template("employees/form.html", employee=None, form={}, errors=[])


@employees_bp.route("/<employee_id>/edit", methods=["GET", "POST"])
@login_required
def edit_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)

    if request.method == "POST":
        errors, data = _validate(request.form)
        if errors:
            return render_template("employees/form.html", employee=employee, form=data, errors=errors)

        employee.name = data["name"]
        employee.phone = data["phone"]
        employee.address = data["address"]
        employee.cnic = data["cnic"]
        employee.email = data["email"]
        employee.is_active = data["is_active"]

        db.session.add(AuditLog(user_id=current_user.id, action="UPDATE", record_type="Employee", record_id=employee.id))
        db.session.commit()
        flash("Employee updated.", "success")
        return redirect(url_for("employees.list_employees"))

    form = {
        "name": employee.name,
        "phone": employee.phone or "",
        "address": employee.address or "",
        "cnic": employee.cnic or "",
        "email": employee.email or "",
        "is_active": employee.is_active,
    }
    return render_template("employees/form.html", employee=employee, form=form, errors=[])
