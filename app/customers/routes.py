from flask import Blueprint, render_template, request
from flask_login import login_required
from sqlalchemy import or_, func

from app.extensions import db
from app.models import Customer, Sale, CustomerPayment
from app.balances import get_debtor_balances, get_debtor_balance

customers_bp = Blueprint("customers", __name__, url_prefix="/customers")


@customers_bp.route("/")
@login_required
def list_customers():
    q = request.args.get("q", "").strip()
    query = db.session.query(
        Customer,
        func.count(Sale.id).filter(Sale.is_deleted.is_(False)).label("total_invoices"),
        func.coalesce(func.sum(Sale.grand_total).filter(Sale.is_deleted.is_(False)), 0).label("total_sales"),
        func.coalesce(func.sum(Sale.cash_amount).filter(Sale.is_deleted.is_(False)), 0).label("total_paid"),
    ).outerjoin(Sale, Sale.customer_id == Customer.id)

    if q:
        like = f"%{q}%"
        query = query.filter(or_(Customer.name.ilike(like), Customer.phone.ilike(like)))

    rows = query.group_by(Customer.id).order_by(Customer.name).all()
    balances = get_debtor_balances([c.id for c, *_ in rows])
    return render_template("customers/list.html", rows=rows, q=q, balances=balances)


@customers_bp.route("/<customer_id>")
@login_required
def view_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    sales = Sale.query.filter_by(customer_id=customer_id, is_deleted=False).order_by(Sale.date.desc()).all()
    payments = CustomerPayment.query.filter_by(customer_id=customer_id).order_by(CustomerPayment.date.desc()).all()
    balance = get_debtor_balance(customer_id)
    return render_template("customers/detail.html", customer=customer, sales=sales, payments=payments, balance=balance)
