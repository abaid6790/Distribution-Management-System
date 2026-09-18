from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import or_

from app.extensions import db
from app.models import Product, AuditLog
from app.stock import get_stock_map

products_bp = Blueprint("products", __name__, url_prefix="/products")


def _round2(n):
    return round(n * 100) / 100


def _validate(form):
    errors = []
    name = form.get("name", "").strip()
    sku = form.get("sku", "").strip()
    category = form.get("category", "").strip()
    packs_per_box = form.get("packs_per_box", "").strip()
    purchase_price_per_box = form.get("purchase_price_per_box", "").strip()
    sale_price_per_box = form.get("sale_price_per_box", "").strip()
    min_stock = form.get("min_stock_level_packs", "0").strip()
    is_active = form.get("is_active") == "on"

    if not name:
        errors.append("Product name is required.")
    if not sku:
        errors.append("SKU is required.")

    try:
        packs_per_box = int(packs_per_box)
        if packs_per_box < 1:
            errors.append("Packs per box must be at least 1.")
    except ValueError:
        errors.append("Packs per box must be a whole number.")
        packs_per_box = 1

    try:
        purchase_price_per_box = float(purchase_price_per_box)
        if purchase_price_per_box < 0:
            errors.append("Purchase price can't be negative.")
    except ValueError:
        errors.append("Enter a valid purchase price.")
        purchase_price_per_box = 0

    try:
        sale_price_per_box = float(sale_price_per_box)
        if sale_price_per_box < 0:
            errors.append("Sale price can't be negative.")
    except ValueError:
        errors.append("Enter a valid sale price.")
        sale_price_per_box = 0

    try:
        min_stock = int(min_stock or 0)
        if min_stock < 0:
            errors.append("Minimum stock can't be negative.")
    except ValueError:
        errors.append("Minimum stock must be a whole number.")
        min_stock = 0

    return errors, {
        "name": name,
        "sku": sku,
        "category": category or None,
        "packs_per_box": packs_per_box,
        "purchase_price_per_box": purchase_price_per_box,
        "sale_price_per_box": sale_price_per_box,
        "min_stock_level_packs": min_stock,
        "is_active": is_active,
    }


@products_bp.route("/")
@login_required
def list_products():
    q = request.args.get("q", "").strip()
    query = Product.query
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Product.name.ilike(like), Product.sku.ilike(like), Product.category.ilike(like)))
    products = query.order_by(Product.name).all()
    stock_map = get_stock_map([p.id for p in products])
    return render_template("products/list.html", products=products, q=q, stock_map=stock_map)


@products_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_product():
    if request.method == "POST":
        errors, data = _validate(request.form)

        if not errors:
            existing = Product.query.filter_by(sku=data["sku"]).first()
            if existing:
                errors.append(f'SKU "{data["sku"]}" is already in use.')

        if errors:
            return render_template("products/form.html", product=None, form=data, errors=errors)

        purchase_pack = _round2(data["purchase_price_per_box"] / data["packs_per_box"])
        sale_pack = _round2(data["sale_price_per_box"] / data["packs_per_box"])

        product = Product(
            name=data["name"],
            category=data["category"],
            sku=data["sku"],
            packs_per_box=data["packs_per_box"],
            purchase_price_per_box=data["purchase_price_per_box"],
            purchase_price_per_pack=purchase_pack,
            sale_price_per_box=data["sale_price_per_box"],
            sale_price_per_pack=sale_pack,
            min_stock_level_packs=data["min_stock_level_packs"],
            is_active=data["is_active"],
        )
        db.session.add(product)
        db.session.flush()
        db.session.add(AuditLog(user_id=current_user.id, action="CREATE", record_type="Product", record_id=product.id))
        db.session.commit()
        flash("Product added.", "success")
        return redirect(url_for("products.list_products"))

    return render_template("products/form.html", product=None, form={}, errors=[])


@products_bp.route("/<product_id>/edit", methods=["GET", "POST"])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == "POST":
        errors, data = _validate(request.form)

        if not errors:
            clash = Product.query.filter(Product.sku == data["sku"], Product.id != product_id).first()
            if clash:
                errors.append(f'SKU "{data["sku"]}" is already in use.')

        if errors:
            return render_template("products/form.html", product=product, form=data, errors=errors)

        purchase_pack = _round2(data["purchase_price_per_box"] / data["packs_per_box"])
        sale_pack = _round2(data["sale_price_per_box"] / data["packs_per_box"])

        product.name = data["name"]
        product.category = data["category"]
        product.sku = data["sku"]
        product.packs_per_box = data["packs_per_box"]
        product.purchase_price_per_box = data["purchase_price_per_box"]
        product.purchase_price_per_pack = purchase_pack
        product.sale_price_per_box = data["sale_price_per_box"]
        product.sale_price_per_pack = sale_pack
        product.min_stock_level_packs = data["min_stock_level_packs"]
        product.is_active = data["is_active"]

        db.session.add(AuditLog(user_id=current_user.id, action="UPDATE", record_type="Product", record_id=product.id))
        db.session.commit()
        flash("Product updated.", "success")
        return redirect(url_for("products.list_products"))

    form = {
        "name": product.name,
        "sku": product.sku,
        "category": product.category or "",
        "packs_per_box": product.packs_per_box,
        "purchase_price_per_box": product.purchase_price_per_box,
        "sale_price_per_box": product.sale_price_per_box,
        "min_stock_level_packs": product.min_stock_level_packs,
        "is_active": product.is_active,
    }
    return render_template("products/form.html", product=product, form=form, errors=[])
