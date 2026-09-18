from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import or_

from app.extensions import db
from app.models import Purchase, PurchaseItem, PurchaseReturn, PurchaseReturnItem, Supplier, Product, Transaction, AuditLog
from app.returns_helpers import get_already_returned_for_purchase_items
from app.invoice_numbers import generate_invoice_number
from app.payments import round2

purchase_returns_bp = Blueprint("purchase_returns", __name__, url_prefix="/purchase-returns")


def _is_future(date_str):
    d = datetime.strptime(date_str, "%Y-%m-%d").date()
    return d > datetime.now().date()


@purchase_returns_bp.route("/")
@login_required
def list_returns():
    rows = (
        db.session.query(PurchaseReturn, Purchase, Supplier)
        .join(Purchase, PurchaseReturn.purchase_id == Purchase.id)
        .join(Supplier, PurchaseReturn.supplier_id == Supplier.id)
        .filter(PurchaseReturn.is_deleted.is_(False))
        .order_by(PurchaseReturn.created_at.desc())
        .all()
    )
    return render_template("purchase_returns/list.html", rows=rows)


@purchase_returns_bp.route("/find")
@login_required
def find_purchase():
    q = request.args.get("q", "").strip()
    results = []
    if q:
        like = f"%{q}%"
        results = (
            db.session.query(Purchase, Supplier)
            .join(Supplier, Purchase.supplier_id == Supplier.id)
            .filter(Purchase.is_deleted.is_(False))
            .filter(or_(Purchase.invoice_number.ilike(like), Supplier.name.ilike(like), Supplier.phone.ilike(like)))
            .order_by(Purchase.created_at.desc())
            .limit(20)
            .all()
        )
    return render_template("purchase_returns/find.html", q=q, results=results)


@purchase_returns_bp.route("/new/<purchase_id>", methods=["GET", "POST"])
@login_required
def new_return(purchase_id):
    purchase = Purchase.query.get_or_404(purchase_id)
    supplier = Supplier.query.get(purchase.supplier_id)
    items = PurchaseItem.query.filter_by(purchase_id=purchase_id).all()
    already_returned = get_already_returned_for_purchase_items([i.id for i in items])

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
        item_ids = request.form.getlist("purchase_item_id[]")
        return_qtys = request.form.getlist("return_qty[]")

        if not date_str:
            errors.append("Date is required.")
        elif _is_future(date_str):
            errors.append("Future dates are not allowed.")

        selected = [(item_ids[i], float(return_qtys[i] or 0)) for i in range(len(item_ids)) if float(return_qtys[i] or 0) > 0]
        if not selected:
            errors.append("Select at least one product to return.")

        if errors:
            return render_template("purchase_returns/new.html", purchase=purchase, supplier=supplier, items_view=items_view, errors=errors, form=request.form)

        try:
            with db.session.begin_nested():
                return_items = []
                for purchase_item_id, qty in selected:
                    view = next((v for v in items_view if v["item"].id == purchase_item_id), None)
                    if not view:
                        raise ValueError("Invalid line selected.")
                    if qty > view["remaining"]:
                        raise ValueError(
                            f'Return quantity for {view["product"].name} exceeds the remaining returnable quantity of {view["remaining"]} packs.'
                        )
                    unit_price_per_pack = float(view["item"].purchase_price_per_pack)
                    line_total = round2(unit_price_per_pack * qty)
                    return_items.append(
                        dict(
                            purchase_item_id=purchase_item_id,
                            product_id=view["item"].product_id,
                            quantity_packs=int(qty),
                            unit_price=unit_price_per_pack,
                            line_total=line_total,
                        )
                    )

                subtotal = round2(sum(i["line_total"] for i in return_items))
                invoice_number = generate_invoice_number("purchase_return")

                purchase_return = PurchaseReturn(
                    return_invoice_number=invoice_number,
                    date=datetime.strptime(date_str, "%Y-%m-%d"),
                    purchase_id=purchase.id,
                    supplier_id=purchase.supplier_id,
                    subtotal=subtotal,
                    grand_total=subtotal,
                    notes=notes or None,
                    created_by_id=current_user.id,
                )
                db.session.add(purchase_return)
                db.session.flush()

                for item in return_items:
                    db.session.add(PurchaseReturnItem(purchase_return_id=purchase_return.id, **item))

                if subtotal > 0:
                    db.session.add(
                        Transaction(
                            date=purchase_return.date,
                            type="CASH_IN",
                            category="PURCHASE_RETURN",
                            description=f"Purchase return {invoice_number} \u2014 {supplier.name}",
                            amount=subtotal,
                            purchase_return_id=purchase_return.id,
                        )
                    )

                db.session.add(
                    AuditLog(user_id=current_user.id, action="CREATE", record_type="PurchaseReturn", record_id=purchase_return.id)
                )

            db.session.commit()
        except ValueError as e:
            db.session.rollback()
            errors.append(str(e))
            return render_template("purchase_returns/new.html", purchase=purchase, supplier=supplier, items_view=items_view, errors=errors, form=request.form)

        flash(f"Purchase return {invoice_number} created.", "success")
        return redirect(url_for("purchase_returns.list_returns"))

    return render_template("purchase_returns/new.html", purchase=purchase, supplier=supplier, items_view=items_view, errors=[], form={})
