from flask import Blueprint, render_template, request
from flask_login import login_required
from sqlalchemy import or_

from app.models import Product
from app.stock import get_stock_detail_map

stock_bp = Blueprint("stock_module", __name__, url_prefix="/stock")


@stock_bp.route("/")
@login_required
def index():
    q = request.args.get("q", "").strip()
    query = Product.query
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Product.name.ilike(like), Product.sku.ilike(like), Product.category.ilike(like)))
    products = query.order_by(Product.name).all()

    detail = get_stock_detail_map([p.id for p in products])

    rows = []
    total_stock_value = 0.0
    total_potential_value = 0.0
    for p in products:
        d = detail.get(p.id, {"purchased": 0, "sold": 0, "sale_returned": 0, "purchase_returned": 0, "remaining": 0})
        remaining = d["remaining"]
        if remaining <= 0:
            status = "out"
        elif remaining < p.min_stock_level_packs:
            status = "low"
        else:
            status = "normal"
        stock_value = remaining * float(p.purchase_price_per_pack)
        potential_value = remaining * float(p.sale_price_per_pack)
        total_stock_value += stock_value
        total_potential_value += potential_value
        rows.append(
            {
                "product": p,
                "purchased": d["purchased"],
                "sold": d["sold"],
                "sale_returned": d["sale_returned"],
                "purchase_returned": d["purchase_returned"],
                "remaining": remaining,
                "status": status,
                "stock_value": stock_value,
                "potential_value": potential_value,
            }
        )

    return render_template(
        "stock_module/index.html",
        rows=rows,
        q=q,
        total_stock_value=total_stock_value,
        total_potential_value=total_potential_value,
    )


@stock_bp.route("/low")
@login_required
def low_stock():
    products = Product.query.filter_by(is_active=True).order_by(Product.name).all()
    detail = get_stock_detail_map([p.id for p in products])

    rows = []
    for p in products:
        remaining = detail.get(p.id, {"remaining": 0})["remaining"]
        if remaining <= 0:
            status = "out"
        elif remaining < p.min_stock_level_packs:
            status = "low"
        else:
            continue
        rows.append({"product": p, "remaining": remaining, "status": status})

    rows.sort(key=lambda r: (r["status"] != "out", r["product"].name))
    return render_template("stock_module/low.html", rows=rows)
