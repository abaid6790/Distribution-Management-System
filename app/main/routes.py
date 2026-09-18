from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from app.dashboard_queries import (
    get_dashboard_summary,
    get_recent_sales,
    get_recent_purchases,
    get_low_stock_products,
    get_recent_transactions,
    get_counts,
)

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return redirect(url_for("main.dashboard"))


@main_bp.route("/dashboard")
@login_required
def dashboard():
    summary = get_dashboard_summary()
    recent_sales = get_recent_sales()
    recent_purchases = get_recent_purchases()
    low_stock = get_low_stock_products()
    recent_tx = get_recent_transactions()
    counts = get_counts()

    first_name = current_user.full_name.split(" ")[0] if current_user.full_name else "there"
    is_empty_business = counts["products"] == 0 and counts["customers"] == 0 and counts["suppliers"] == 0

    return render_template(
        "dashboard.html",
        summary=summary,
        recent_sales=recent_sales,
        recent_purchases=recent_purchases,
        low_stock=low_stock,
        recent_tx=recent_tx,
        counts=counts,
        first_name=first_name,
        is_empty_business=is_empty_business,
    )
