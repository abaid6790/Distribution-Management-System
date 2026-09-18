from flask import Blueprint, render_template, request
from flask_login import login_required
from sqlalchemy import or_, func

from app.extensions import db
from app.models import Supplier, Purchase, SupplierPayment
from app.balances import get_creditor_balances, get_creditor_balance

suppliers_bp = Blueprint("suppliers", __name__, url_prefix="/suppliers")


@suppliers_bp.route("/")
@login_required
def list_suppliers():
    q = request.args.get("q", "").strip()
    query = db.session.query(
        Supplier,
        func.count(Purchase.id).filter(Purchase.is_deleted.is_(False)).label("total_invoices"),
        func.coalesce(func.sum(Purchase.grand_total).filter(Purchase.is_deleted.is_(False)), 0).label("total_purchases"),
        func.coalesce(func.sum(Purchase.cash_amount).filter(Purchase.is_deleted.is_(False)), 0).label("total_paid"),
    ).outerjoin(Purchase, Purchase.supplier_id == Supplier.id)

    if q:
        like = f"%{q}%"
        query = query.filter(or_(Supplier.name.ilike(like), Supplier.phone.ilike(like)))

    rows = query.group_by(Supplier.id).order_by(Supplier.name).all()
    balances = get_creditor_balances([s.id for s, *_ in rows])
    return render_template("suppliers/list.html", rows=rows, q=q, balances=balances)


@suppliers_bp.route("/<supplier_id>")
@login_required
def view_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    purchases = Purchase.query.filter_by(supplier_id=supplier_id, is_deleted=False).order_by(Purchase.date.desc()).all()
    payments = SupplierPayment.query.filter_by(supplier_id=supplier_id).order_by(SupplierPayment.date.desc()).all()
    balance = get_creditor_balance(supplier_id)
    return render_template("suppliers/detail.html", supplier=supplier, purchases=purchases, payments=payments, balance=balance)
