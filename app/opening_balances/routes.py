from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from app.extensions import db
from app.models import OpeningStock, OpeningDebtor, OpeningCreditor, Product, Customer, Supplier
from app.parties import find_or_create_customer, find_or_create_supplier

opening_bp = Blueprint("opening_balances", __name__, url_prefix="/stock/opening")


def _is_future(date_str):
    d = datetime.strptime(date_str, "%Y-%m-%d").date()
    return d > datetime.now().date()


@opening_bp.route("/")
@login_required
def index():
    tab = request.args.get("tab", "stock")

    context = {"tab": tab, "errors": [], "form": {}}

    if tab == "stock":
        context["rows"] = (
            db.session.query(OpeningStock, Product)
            .join(Product, OpeningStock.product_id == Product.id)
            .order_by(OpeningStock.created_at.desc())
            .all()
        )
        context["products"] = Product.query.order_by(Product.name).all()
    elif tab == "debtors":
        context["rows"] = (
            db.session.query(OpeningDebtor, Customer)
            .join(Customer, OpeningDebtor.customer_id == Customer.id)
            .order_by(OpeningDebtor.created_at.desc())
            .all()
        )
    elif tab == "creditors":
        context["rows"] = (
            db.session.query(OpeningCreditor, Supplier)
            .join(Supplier, OpeningCreditor.supplier_id == Supplier.id)
            .order_by(OpeningCreditor.created_at.desc())
            .all()
        )

    return render_template("opening_balances/index.html", **context)


@opening_bp.route("/stock", methods=["POST"])
@login_required
def add_opening_stock():
    errors = []
    product_id = request.form.get("product_id", "")
    date_str = request.form.get("date", "")
    notes = request.form.get("notes", "").strip()

    product = Product.query.get(product_id)
    if not product:
        errors.append("Select a valid product.")

    try:
        quantity = int(request.form.get("quantity_packs", "0"))
        if quantity <= 0:
            errors.append("Quantity must be greater than 0.")
    except ValueError:
        quantity = 0
        errors.append("Enter a valid whole number of packs.")

    try:
        cost = float(request.form.get("cost_per_pack", "0"))
        if cost < 0:
            errors.append("Cost can't be negative.")
    except ValueError:
        cost = 0
        errors.append("Enter a valid cost per pack.")

    if not date_str:
        errors.append("Date is required.")
    elif _is_future(date_str):
        errors.append("Future dates are not allowed.")

    if errors:
        products = Product.query.order_by(Product.name).all()
        rows = db.session.query(OpeningStock, Product).join(Product, OpeningStock.product_id == Product.id).order_by(OpeningStock.created_at.desc()).all()
        return render_template("opening_balances/index.html", tab="stock", products=products, rows=rows, errors=errors, form=request.form)

    db.session.add(
        OpeningStock(
            product_id=product.id,
            quantity_packs=quantity,
            cost_per_pack=round(cost, 2),
            date=datetime.strptime(date_str, "%Y-%m-%d"),
            notes=notes or None,
        )
    )
    db.session.commit()
    flash(f"Opening stock recorded for {product.name}.", "success")
    return redirect(url_for("opening_balances.index", tab="stock"))


@opening_bp.route("/debtors", methods=["POST"])
@login_required
def add_opening_debtor():
    errors = []
    name = request.form.get("customer_name", "").strip()
    phone = request.form.get("customer_phone", "").strip()
    address = request.form.get("customer_address", "").strip()
    date_str = request.form.get("date", "")
    notes = request.form.get("notes", "").strip()

    if not name or not phone or not address:
        errors.append("Customer name, phone, and address are required.")

    try:
        amount = float(request.form.get("amount", "0"))
        if amount <= 0:
            errors.append("Amount must be greater than 0.")
    except ValueError:
        amount = 0
        errors.append("Enter a valid amount.")

    if not date_str:
        errors.append("Date is required.")
    elif _is_future(date_str):
        errors.append("Future dates are not allowed.")

    if errors:
        rows = db.session.query(OpeningDebtor, Customer).join(Customer, OpeningDebtor.customer_id == Customer.id).order_by(OpeningDebtor.created_at.desc()).all()
        return render_template("opening_balances/index.html", tab="debtors", rows=rows, errors=errors, form=request.form)

    customer = find_or_create_customer(name, phone, address)
    db.session.add(
        OpeningDebtor(
            customer_id=customer.id,
            amount=round(amount, 2),
            date=datetime.strptime(date_str, "%Y-%m-%d"),
            notes=notes or None,
        )
    )
    db.session.commit()
    flash(f"Opening balance recorded for {customer.name}.", "success")
    return redirect(url_for("opening_balances.index", tab="debtors"))


@opening_bp.route("/creditors", methods=["POST"])
@login_required
def add_opening_creditor():
    errors = []
    name = request.form.get("supplier_name", "").strip()
    phone = request.form.get("supplier_phone", "").strip()
    address = request.form.get("supplier_address", "").strip()
    date_str = request.form.get("date", "")
    notes = request.form.get("notes", "").strip()

    if not name or not phone or not address:
        errors.append("Supplier name, phone, and address are required.")

    try:
        amount = float(request.form.get("amount", "0"))
        if amount <= 0:
            errors.append("Amount must be greater than 0.")
    except ValueError:
        amount = 0
        errors.append("Enter a valid amount.")

    if not date_str:
        errors.append("Date is required.")
    elif _is_future(date_str):
        errors.append("Future dates are not allowed.")

    if errors:
        rows = db.session.query(OpeningCreditor, Supplier).join(Supplier, OpeningCreditor.supplier_id == Supplier.id).order_by(OpeningCreditor.created_at.desc()).all()
        return render_template("opening_balances/index.html", tab="creditors", rows=rows, errors=errors, form=request.form)

    supplier = find_or_create_supplier(name, phone, address)
    db.session.add(
        OpeningCreditor(
            supplier_id=supplier.id,
            amount=round(amount, 2),
            date=datetime.strptime(date_str, "%Y-%m-%d"),
            notes=notes or None,
        )
    )
    db.session.commit()
    flash(f"Opening balance recorded for {supplier.name}.", "success")
    return redirect(url_for("opening_balances.index", tab="creditors"))
