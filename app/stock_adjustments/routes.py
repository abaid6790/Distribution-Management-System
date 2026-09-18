from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.extensions import db
from app.models import StockAdjustment, Product, AuditLog
from app.stock import get_stock_for_product

stock_adjustments_bp = Blueprint("stock_adjustments", __name__, url_prefix="/stock/adjustments")

ADJUSTMENT_TYPES = ["DAMAGED", "LOST", "BROKEN", "PHYSICAL_COUNT", "CORRECTION", "OTHER"]
TYPE_LABELS = {
    "DAMAGED": "Damaged",
    "LOST": "Lost",
    "BROKEN": "Broken",
    "PHYSICAL_COUNT": "Physical Count",
    "CORRECTION": "Correction",
    "OTHER": "Other",
}


def _is_future(date_str):
    d = datetime.strptime(date_str, "%Y-%m-%d").date()
    return d > datetime.now().date()


@stock_adjustments_bp.route("/")
@login_required
def list_adjustments():
    rows = (
        db.session.query(StockAdjustment, Product)
        .join(Product, StockAdjustment.product_id == Product.id)
        .order_by(StockAdjustment.created_at.desc())
        .all()
    )
    return render_template("stock_adjustments/list.html", rows=rows, type_labels=TYPE_LABELS)


@stock_adjustments_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_adjustment():
    products = Product.query.filter_by(is_active=True).order_by(Product.name).all()

    if request.method == "POST":
        errors = []
        product_id = request.form.get("product_id", "")
        direction = request.form.get("direction", "decrease")
        adj_type = request.form.get("type", "")
        reason = request.form.get("reason", "").strip()
        date_str = request.form.get("date", "")
        notes = request.form.get("notes", "").strip()

        product = Product.query.get(product_id)
        if not product:
            errors.append("Select a valid product.")

        try:
            quantity = int(request.form.get("quantity", "0"))
            if quantity <= 0:
                errors.append("Quantity must be greater than 0.")
        except ValueError:
            quantity = 0
            errors.append("Enter a valid whole number of packs.")

        if not adj_type or adj_type not in ADJUSTMENT_TYPES:
            errors.append("Select an adjustment type.")
        if not reason:
            errors.append("A reason is required.")
        if not date_str:
            errors.append("Date is required.")
        elif _is_future(date_str):
            errors.append("Future dates are not allowed.")

        signed_qty = quantity if direction == "increase" else -quantity

        if not errors and product and direction == "decrease":
            current = get_stock_for_product(product.id)
            if quantity > current:
                errors.append(f"Can't remove {quantity} packs — only {int(current)} packs are currently in stock.")

        if errors:
            return render_template(
                "stock_adjustments/form.html", products=products, types=ADJUSTMENT_TYPES, type_labels=TYPE_LABELS, errors=errors, form=request.form
            )

        adjustment = StockAdjustment(
            product_id=product.id,
            quantity_packs=signed_qty,
            type=adj_type,
            reason=reason,
            date=datetime.strptime(date_str, "%Y-%m-%d"),
            user_id=current_user.id,
            notes=notes or None,
        )
        db.session.add(adjustment)
        db.session.flush()

        db.session.add(
            AuditLog(user_id=current_user.id, action="ADJUSTMENT", record_type="StockAdjustment", record_id=adjustment.id)
        )
        db.session.commit()
        flash(f"Stock adjustment recorded for {product.name}.", "success")
        return redirect(url_for("stock_adjustments.list_adjustments"))

    return render_template(
        "stock_adjustments/form.html", products=products, types=ADJUSTMENT_TYPES, type_labels=TYPE_LABELS, errors=[], form={}
    )
