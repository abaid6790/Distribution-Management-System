from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Supplier, SupplierPayment, Transaction, AuditLog, Purchase
from app.balances import get_creditor_balances

creditors_bp = Blueprint("creditors", __name__, url_prefix="/creditors")


def _is_future(date_str):
    d = datetime.strptime(date_str, "%Y-%m-%d").date()
    return d > datetime.now().date()


@creditors_bp.route("/")
@login_required
def list_creditors():
    suppliers = Supplier.query.order_by(Supplier.name).all()
    balances = get_creditor_balances([s.id for s in suppliers])
    rows = [
        {"supplier": s, "balance": balances.get(s.id, {"total_credit": 0, "total_paid": 0, "pending": 0})}
        for s in suppliers
    ]
    rows = [r for r in rows if r["balance"]["pending"] > 0.01]
    rows.sort(key=lambda r: r["balance"]["pending"], reverse=True)
    return render_template("creditors/list.html", rows=rows)


@creditors_bp.route("/<supplier_id>/pay", methods=["POST"])
@login_required
def pay_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    balance = get_creditor_balances([supplier_id]).get(supplier_id, {"pending": 0})

    date_str = request.form.get("date", "")
    payment_method = request.form.get("payment_method", "CASH")
    notes = request.form.get("notes", "").strip()

    error = None
    try:
        amount = float(request.form.get("amount", "0"))
    except ValueError:
        amount = 0
        error = "Enter a valid amount."

    if not error and amount <= 0:
        error = "Payment amount must be greater than 0."
    if not error and amount > balance["pending"] + 0.01:
        error = "Payment can't exceed the outstanding balance."
    if not error and not date_str:
        error = "Date is required."
    elif not error and _is_future(date_str):
        error = "Future dates are not allowed."

    if error:
        purchases = Purchase.query.filter_by(supplier_id=supplier_id, is_deleted=False).order_by(Purchase.date.desc()).all()
        payments = SupplierPayment.query.filter_by(supplier_id=supplier_id).order_by(SupplierPayment.date.desc()).all()
        return render_template(
            "suppliers/detail.html", supplier=supplier, purchases=purchases, payments=payments, balance=balance, payment_error=error
        )

    payment = SupplierPayment(
        supplier_id=supplier_id,
        amount=round(amount, 2),
        date=datetime.strptime(date_str, "%Y-%m-%d"),
        payment_method=payment_method,
        notes=notes or None,
        user_id=current_user.id,
    )
    db.session.add(payment)
    db.session.flush()

    db.session.add(
        Transaction(
            date=payment.date,
            type="CASH_OUT",
            category="SUPPLIER_PAYMENT",
            description=f"Payment made \u2014 {supplier.name}",
            amount=payment.amount,
            supplier_payment_id=payment.id,
        )
    )
    db.session.add(AuditLog(user_id=current_user.id, action="PAYMENT", record_type="SupplierPayment", record_id=payment.id))
    db.session.commit()

    flash(f"Payment of {payment.amount:,.2f} recorded to {supplier.name}.", "success")
    return redirect(url_for("suppliers.view_supplier", supplier_id=supplier_id))
