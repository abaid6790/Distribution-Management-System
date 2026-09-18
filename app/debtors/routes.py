from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Customer, CustomerPayment, Transaction, AuditLog
from app.balances import get_debtor_balances

debtors_bp = Blueprint("debtors", __name__, url_prefix="/debtors")


def _is_future(date_str):
    d = datetime.strptime(date_str, "%Y-%m-%d").date()
    return d > datetime.now().date()


@debtors_bp.route("/")
@login_required
def list_debtors():
    customers = Customer.query.order_by(Customer.name).all()
    balances = get_debtor_balances([c.id for c in customers])
    rows = [
        {"customer": c, "balance": balances.get(c.id, {"total_credit": 0, "total_paid": 0, "pending": 0})}
        for c in customers
    ]
    rows = [r for r in rows if r["balance"]["pending"] > 0.01]
    rows.sort(key=lambda r: r["balance"]["pending"], reverse=True)
    return render_template("debtors/list.html", rows=rows)


@debtors_bp.route("/<customer_id>/pay", methods=["POST"])
@login_required
def receive_payment(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    balance = get_debtor_balances([customer_id]).get(customer_id, {"pending": 0})

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
        from app.models import Sale

        sales = Sale.query.filter_by(customer_id=customer_id, is_deleted=False).order_by(Sale.date.desc()).all()
        payments = CustomerPayment.query.filter_by(customer_id=customer_id).order_by(CustomerPayment.date.desc()).all()
        return render_template(
            "customers/detail.html", customer=customer, sales=sales, payments=payments, balance=balance, payment_error=error
        )

    payment = CustomerPayment(
        customer_id=customer_id,
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
            type="CASH_IN",
            category="CUSTOMER_PAYMENT",
            description=f"Payment received \u2014 {customer.name}",
            amount=payment.amount,
            customer_payment_id=payment.id,
        )
    )
    db.session.add(AuditLog(user_id=current_user.id, action="PAYMENT", record_type="CustomerPayment", record_id=payment.id))
    db.session.commit()

    flash(f"Payment of {payment.amount:,.2f} recorded for {customer.name}.", "success")
    return redirect(url_for("customers.view_customer", customer_id=customer_id))
