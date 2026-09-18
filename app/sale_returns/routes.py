from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import or_

from app.extensions import db
from app.models import Sale, SaleItem, SaleReturn, SaleReturnItem, Customer, Product, Transaction, AuditLog
from app.returns_helpers import get_already_returned_for_sale_items
from app.invoice_numbers import generate_invoice_number
from app.payments import round2

sale_returns_bp = Blueprint("sale_returns", __name__, url_prefix="/sale-returns")


def _is_future(date_str):
    d = datetime.strptime(date_str, "%Y-%m-%d").date()
    return d > datetime.now().date()


@sale_returns_bp.route("/")
@login_required
def list_returns():
    rows = (
        db.session.query(SaleReturn, Sale, Customer)
        .join(Sale, SaleReturn.sale_id == Sale.id)
        .join(Customer, SaleReturn.customer_id == Customer.id)
        .filter(SaleReturn.is_deleted.is_(False))
        .order_by(SaleReturn.created_at.desc())
        .all()
    )
    return render_template("sale_returns/list.html", rows=rows)


@sale_returns_bp.route("/find")
@login_required
def find_sale():
    q = request.args.get("q", "").strip()
    results = []
    if q:
        like = f"%{q}%"
        results = (
            db.session.query(Sale, Customer)
            .join(Customer, Sale.customer_id == Customer.id)
            .filter(Sale.is_deleted.is_(False))
            .filter(or_(Sale.invoice_number.ilike(like), Customer.name.ilike(like), Customer.phone.ilike(like)))
            .order_by(Sale.created_at.desc())
            .limit(20)
            .all()
        )
    return render_template("sale_returns/find.html", q=q, results=results)


@sale_returns_bp.route("/new/<sale_id>", methods=["GET", "POST"])
@login_required
def new_return(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    customer = Customer.query.get(sale.customer_id)
    items = SaleItem.query.filter_by(sale_id=sale_id).all()
    already_returned = get_already_returned_for_sale_items([i.id for i in items])

    items_view = []
    for i in items:
        product = Product.query.get(i.product_id)
        returned = already_returned.get(i.id, 0)
        items_view.append(
            {
                "item": i,
                "product": product,
                "already_returned": returned,
                "remaining": i.quantity_packs - returned,
            }
        )

    if request.method == "POST":
        errors = []
        date_str = request.form.get("date", "")
        notes = request.form.get("notes", "").strip()
        item_ids = request.form.getlist("sale_item_id[]")
        return_qtys = request.form.getlist("return_qty[]")

        if not date_str:
            errors.append("Date is required.")
        elif _is_future(date_str):
            errors.append("Future dates are not allowed.")

        selected = [(item_ids[i], float(return_qtys[i] or 0)) for i in range(len(item_ids)) if float(return_qtys[i] or 0) > 0]
        if not selected:
            errors.append("Select at least one product to return.")

        if errors:
            return render_template("sale_returns/new.html", sale=sale, customer=customer, items_view=items_view, errors=errors, form=request.form)

        try:
            with db.session.begin_nested():
                return_items = []
                for sale_item_id, qty in selected:
                    view = next((v for v in items_view if v["item"].id == sale_item_id), None)
                    if not view:
                        raise ValueError("Invalid line selected.")
                    if qty > view["remaining"]:
                        raise ValueError(
                            f'Return quantity for {view["product"].name} exceeds the remaining returnable quantity of {view["remaining"]} packs.'
                        )
                    unit_price_per_pack = round2(
                        (float(view["item"].unit_price) * float(view["item"].quantity)) / view["item"].quantity_packs
                    )
                    line_total = round2(unit_price_per_pack * qty)
                    return_items.append(
                        dict(
                            sale_item_id=sale_item_id,
                            product_id=view["item"].product_id,
                            quantity_packs=int(qty),
                            unit_price=unit_price_per_pack,
                            line_total=line_total,
                        )
                    )

                subtotal = round2(sum(i["line_total"] for i in return_items))
                invoice_number = generate_invoice_number("sale_return")

                sale_return = SaleReturn(
                    return_invoice_number=invoice_number,
                    date=datetime.strptime(date_str, "%Y-%m-%d"),
                    sale_id=sale.id,
                    customer_id=sale.customer_id,
                    subtotal=subtotal,
                    grand_total=subtotal,
                    notes=notes or None,
                    created_by_id=current_user.id,
                )
                db.session.add(sale_return)
                db.session.flush()

                for item in return_items:
                    db.session.add(SaleReturnItem(sale_return_id=sale_return.id, **item))

                if subtotal > 0:
                    db.session.add(
                        Transaction(
                            date=sale_return.date,
                            type="CASH_OUT",
                            category="SALE_RETURN",
                            description=f"Sale return {invoice_number} \u2014 {customer.name}",
                            amount=subtotal,
                            sale_return_id=sale_return.id,
                        )
                    )

                db.session.add(
                    AuditLog(user_id=current_user.id, action="CREATE", record_type="SaleReturn", record_id=sale_return.id)
                )

            db.session.commit()
        except ValueError as e:
            db.session.rollback()
            errors.append(str(e))
            return render_template("sale_returns/new.html", sale=sale, customer=customer, items_view=items_view, errors=errors, form=request.form)

        flash(f"Sale return {invoice_number} created.", "success")
        return redirect(url_for("sale_returns.list_returns"))

    return render_template("sale_returns/new.html", sale=sale, customer=customer, items_view=items_view, errors=[], form={})
