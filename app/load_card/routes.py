from datetime import datetime, timedelta

from flask import Blueprint, render_template, request
from flask_login import login_required

from app.extensions import db
from app.models import Sale, SaleItem, Customer, Employee, Product

load_card_bp = Blueprint("load_card", __name__, url_prefix="/load-card")


@load_card_bp.route("/")
@login_required
def index():
    date_str = request.args.get("date") or datetime.now().date().isoformat()
    salesman_id = request.args.get("salesman_id", "")
    customer_id = request.args.get("customer_id", "")
    product_id = request.args.get("product_id", "")

    day_start = datetime.strptime(date_str, "%Y-%m-%d")
    day_end = day_start + timedelta(days=1)

    query = (
        db.session.query(
            Customer.name.label("customer_name"),
            Product.name.label("product_name"),
            SaleItem.quantity_packs,
            SaleItem.line_total,
        )
        .join(Sale, SaleItem.sale_id == Sale.id)
        .join(Customer, Sale.customer_id == Customer.id)
        .join(Product, SaleItem.product_id == Product.id)
        .filter(Sale.is_deleted.is_(False), Sale.date >= day_start, Sale.date < day_end)
    )

    if salesman_id:
        query = query.filter(Sale.booked_by_id == salesman_id)
    if customer_id:
        query = query.filter(Sale.customer_id == customer_id)
    if product_id:
        query = query.filter(SaleItem.product_id == product_id)

    raw_rows = query.all()

    grouped = {}
    for r in raw_rows:
        key = (r.customer_name, r.product_name)
        if key not in grouped:
            grouped[key] = {"customer": r.customer_name, "product": r.product_name, "quantity": 0, "total": 0.0}
        grouped[key]["quantity"] += r.quantity_packs
        grouped[key]["total"] += float(r.line_total)

    rows = sorted(grouped.values(), key=lambda r: (r["customer"], r["product"]))
    grand_total = sum(r["total"] for r in rows)

    employees = Employee.query.order_by(Employee.name).all()
    customers = Customer.query.order_by(Customer.name).all()
    products = Product.query.order_by(Product.name).all()

    return render_template(
        "load_card/index.html",
        rows=rows,
        grand_total=grand_total,
        date_str=date_str,
        salesman_id=salesman_id,
        customer_id=customer_id,
        product_id=product_id,
        employees=employees,
        customers=customers,
        products=products,
    )
