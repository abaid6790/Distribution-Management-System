from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Expense, Transaction, AuditLog

expenses_bp = Blueprint("expenses", __name__, url_prefix="/expenses")

CATEGORIES = ["Transport", "Fuel", "Rent", "Electricity", "Salary", "Loading", "Unloading", "Maintenance", "Other"]


def _is_future(date_str):
    d = datetime.strptime(date_str, "%Y-%m-%d").date()
    return d > datetime.now().date()


@expenses_bp.route("/")
@login_required
def list_expenses():
    rows = Expense.query.order_by(Expense.date.desc(), Expense.created_at.desc()).all()
    total = sum(float(r.amount) for r in rows)
    return render_template("expenses/list.html", rows=rows, total=total, categories=CATEGORIES)


@expenses_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_expense():
    if request.method == "POST":
        errors = []
        date_str = request.form.get("date", "")
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        payment_method = request.form.get("payment_method", "CASH")
        notes = request.form.get("notes", "").strip()

        try:
            amount = float(request.form.get("amount", "0"))
        except ValueError:
            amount = 0
            errors.append("Enter a valid amount.")

        if not date_str:
            errors.append("Date is required.")
        elif _is_future(date_str):
            errors.append("Future dates are not allowed.")
        if not category:
            errors.append("Category is required.")
        if not description:
            errors.append("Description is required.")
        if amount <= 0:
            errors.append("Amount must be greater than 0.")

        if errors:
            return render_template("expenses/form.html", categories=CATEGORIES, errors=errors, form=request.form)

        expense = Expense(
            date=datetime.strptime(date_str, "%Y-%m-%d"),
            category=category,
            description=description,
            amount=round(amount, 2),
            payment_method=payment_method,
            notes=notes or None,
            user_id=current_user.id,
        )
        db.session.add(expense)
        db.session.flush()

        if payment_method != "CREDIT":
            db.session.add(
                Transaction(
                    date=expense.date,
                    type="CASH_OUT",
                    category="EXPENSE",
                    description=f"{category} \u2014 {description}",
                    amount=expense.amount,
                    expense_id=expense.id,
                )
            )

        db.session.add(AuditLog(user_id=current_user.id, action="CREATE", record_type="Expense", record_id=expense.id))
        db.session.commit()
        flash("Expense recorded.", "success")
        return redirect(url_for("expenses.list_expenses"))

    return render_template("expenses/form.html", categories=CATEGORIES, errors=[], form={})
