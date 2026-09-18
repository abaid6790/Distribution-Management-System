from flask import Blueprint, render_template, request

from flask_login import login_required

from app.date_ranges import resolve_range
from app.reports_queries import (
    get_sales_report,
    get_purchase_report,
    get_expense_report,
    get_sale_return_report,
    get_purchase_return_report,
    get_debtor_report,
    get_creditor_report,
    get_profit_and_loss,
)
from app.models import Product
from app.stock import get_stock_detail_map

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")

DATE_RANGED_TABS = {"pnl", "sales", "purchases", "expenses", "sale_returns", "purchase_returns"}


@reports_bp.route("/")
@login_required
def index():
    tab = request.args.get("tab", "pnl")
    range_key = request.args.get("range", "today")
    from_str = request.args.get("from", "")
    to_str = request.args.get("to", "")

    context = {"tab": tab, "range_key": range_key, "from_str": from_str, "to_str": to_str}

    if tab in DATE_RANGED_TABS:
        start, end, label = resolve_range(range_key, from_str, to_str)
        context["range_label"] = label

        if tab == "pnl":
            context["pnl"] = get_profit_and_loss(start, end)
        elif tab == "sales":
            context["rows"] = get_sales_report(start, end)
        elif tab == "purchases":
            context["rows"] = get_purchase_report(start, end)
        elif tab == "expenses":
            context["rows"] = get_expense_report(start, end)
        elif tab == "sale_returns":
            context["rows"] = get_sale_return_report(start, end)
        elif tab == "purchase_returns":
            context["rows"] = get_purchase_return_report(start, end)

    elif tab == "debtors":
        context["rows"] = get_debtor_report()

    elif tab == "creditors":
        context["rows"] = get_creditor_report()

    elif tab == "stock":
        products = Product.query.order_by(Product.name).all()
        detail = get_stock_detail_map([p.id for p in products])
        rows = []
        for p in products:
            d = detail.get(p.id, {"purchased": 0, "sold": 0, "sale_returned": 0, "purchase_returned": 0, "remaining": 0})
            rows.append(
                {
                    "product": p,
                    "purchased": d["purchased"],
                    "sold": d["sold"],
                    "sale_returned": d["sale_returned"],
                    "purchase_returned": d["purchase_returned"],
                    "remaining": d["remaining"],
                    "stock_value": d["remaining"] * float(p.purchase_price_per_pack),
                    "potential_value": d["remaining"] * float(p.sale_price_per_pack),
                }
            )
        context["rows"] = rows

    return render_template("reports/index.html", **context)
