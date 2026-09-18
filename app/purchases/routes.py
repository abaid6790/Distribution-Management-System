import json
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import or_

from app.extensions import db
from app.models import Purchase, PurchaseItem, Product, Supplier, Transaction, AuditLog, PurchaseReturn
from app.parties import find_or_create_supplier
from app.invoice_numbers import generate_invoice_number
from app.payments import resolve_payment, round2
from app.stock import get_stock_map

purchases_bp = Blueprint("purchases", __name__, url_prefix="/purchases")


def _is_future(date_str):
    d = datetime.strptime(date_str, "%Y-%m-%d").date()
    return d > datetime.now().date()


def _products_json(products):
    return json.dumps(
        [
            {
                "id": p.id,
                "name": p.name,
                "sku": p.sku,
                "packs_per_box": p.packs_per_box,
                "purchase_price_per_box": float(p.purchase_price_per_box),
                "sale_price_per_box": float(p.sale_price_per_box),
            }
            for p in products
        ]
    )


@purchases_bp.route("/")
@login_required
def list_purchases():
    q = request.args.get("q", "").strip()
    query = Purchase.query.join(Supplier, Purchase.supplier_id == Supplier.id).filter(Purchase.is_deleted.is_(False))
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Purchase.invoice_number.ilike(like), Supplier.name.ilike(like), Supplier.phone.ilike(like)))
    rows = query.order_by(Purchase.created_at.desc()).all()
    return render_template("purchases/list.html", rows=rows, q=q)


@purchases_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_purchase():
    products = Product.query.filter_by(is_active=True).order_by(Product.name).all()

    if request.method == "POST":
        errors = []
        date_str = request.form.get("date", "")
        supplier_name = request.form.get("supplier_name", "").strip()
        supplier_phone = request.form.get("supplier_phone", "").strip()
        supplier_address = request.form.get("supplier_address", "").strip()

        modes = request.form.getlist("mode[]")
        product_ids = request.form.getlist("product_id[]")
        new_names = request.form.getlist("new_name[]")
        new_categories = request.form.getlist("new_category[]")
        new_skus = request.form.getlist("new_sku[]")
        new_packs = request.form.getlist("new_packs_per_box[]")
        new_min_stock = request.form.getlist("new_min_stock[]")
        quantity_boxes = request.form.getlist("quantity_boxes[]")
        purchase_prices = request.form.getlist("purchase_price_per_box[]")
        sale_prices = request.form.getlist("sale_price_per_box[]")
        discounts = request.form.getlist("discount[]")

        overall_discount = request.form.get("overall_discount", "0")
        tax = request.form.get("tax", "0")
        payment_method = request.form.get("payment_method", "CASH")
        cash_amount = request.form.get("cash_amount", "0")
        notes = request.form.get("notes", "").strip()

        if not date_str:
            errors.append("Date is required.")
        elif _is_future(date_str):
            errors.append("Future dates are not allowed.")
        if not supplier_name or not supplier_phone or not supplier_address:
            errors.append("Supplier name, phone, and address are required.")
        if not modes:
            errors.append("Add at least one product.")

        def refetch_and_render():
            return render_template(
                "purchases/form.html",
                products=products,
                products_json=_products_json(products),
                errors=errors,
                form=request.form,
            )

        if errors:
            return refetch_and_render()

        try:
            with db.session.begin_nested():
                supplier = find_or_create_supplier(supplier_name, supplier_phone, supplier_address)

                prepared_items = []
                for i in range(len(modes)):
                    mode = modes[i]
                    qty_boxes = float(quantity_boxes[i] or 0)
                    purchase_price_box = float(purchase_prices[i] or 0)
                    sale_price_box = float(sale_prices[i] or 0)
                    discount = float(discounts[i] or 0)

                    if qty_boxes <= 0:
                        raise ValueError("Every line needs a quantity greater than 0.")

                    if mode == "new":
                        sku = new_skus[i].strip()
                        if not sku or not new_names[i].strip():
                            raise ValueError("New products need at least a name and SKU.")
                        if Product.query.filter_by(sku=sku).first():
                            raise ValueError(f'SKU "{sku}" already exists. Select it instead of creating new.')
                        packs_per_box = int(new_packs[i] or 1)
                        purchase_pack = round2(purchase_price_box / packs_per_box)
                        sale_pack = round2(sale_price_box / packs_per_box)
                        product = Product(
                            name=new_names[i].strip(),
                            category=new_categories[i].strip() or None,
                            sku=sku,
                            packs_per_box=packs_per_box,
                            purchase_price_per_box=purchase_price_box,
                            purchase_price_per_pack=purchase_pack,
                            sale_price_per_box=sale_price_box,
                            sale_price_per_pack=sale_pack,
                            min_stock_level_packs=int(new_min_stock[i] or 0),
                        )
                        db.session.add(product)
                        db.session.flush()
                    else:
                        product = Product.query.get(product_ids[i])
                        if not product:
                            raise ValueError("One of the selected products no longer exists.")
                        packs_per_box = product.packs_per_box
                        purchase_pack = round2(purchase_price_box / packs_per_box)
                        sale_pack = round2(sale_price_box / packs_per_box)
                        product.purchase_price_per_box = purchase_price_box
                        product.purchase_price_per_pack = purchase_pack
                        product.sale_price_per_box = sale_price_box
                        product.sale_price_per_pack = sale_pack

                    quantity_packs = round(qty_boxes * packs_per_box)
                    line_total = round2(purchase_price_box * qty_boxes - discount)
                    if line_total < 0:
                        raise ValueError("A line discount can't exceed that line's total.")

                    prepared_items.append(
                        dict(
                            product_id=product.id,
                            packs_per_box_snapshot=packs_per_box,
                            quantity_boxes=qty_boxes,
                            quantity_packs=quantity_packs,
                            purchase_price_per_box=purchase_price_box,
                            purchase_price_per_pack=purchase_pack,
                            sale_price_per_box=sale_price_box,
                            sale_price_per_pack=sale_pack,
                            discount=discount,
                            line_total=line_total,
                        )
                    )

                subtotal = round2(sum(i["line_total"] for i in prepared_items))
                grand_total = round2(subtotal - float(overall_discount or 0) + float(tax or 0))
                if grand_total < 0:
                    raise ValueError("Overall discount can't exceed the subtotal plus tax.")

                payment = resolve_payment(grand_total, payment_method, float(cash_amount or 0))
                if payment.error:
                    raise ValueError(payment.error)

                invoice_number = generate_invoice_number("purchase")

                purchase = Purchase(
                    invoice_number=invoice_number,
                    date=datetime.strptime(date_str, "%Y-%m-%d"),
                    supplier_id=supplier.id,
                    subtotal=subtotal,
                    overall_discount=float(overall_discount or 0),
                    tax=float(tax or 0),
                    grand_total=grand_total,
                    cash_amount=payment.cash_amount,
                    credit_amount=payment.credit_amount,
                    payment_method=payment_method,
                    payment_status=payment.payment_status,
                    notes=notes or None,
                    created_by_id=current_user.id,
                )
                db.session.add(purchase)
                db.session.flush()

                for item in prepared_items:
                    db.session.add(PurchaseItem(purchase_id=purchase.id, **item))

                if payment.cash_amount > 0:
                    db.session.add(
                        Transaction(
                            date=purchase.date,
                            type="CASH_OUT",
                            category="PURCHASE",
                            description=f"Purchase {invoice_number} \u2014 {supplier.name}",
                            amount=payment.cash_amount,
                            purchase_id=purchase.id,
                        )
                    )

                db.session.add(
                    AuditLog(user_id=current_user.id, action="CREATE", record_type="Purchase", record_id=purchase.id)
                )

            db.session.commit()
        except ValueError as e:
            db.session.rollback()
            errors.append(str(e))
            return refetch_and_render()

        flash(f"Purchase {invoice_number} created.", "success")
        return redirect(url_for("purchases.list_purchases"))

    return render_template("purchases/form.html", products=products, products_json=_products_json(products), errors=[], form={})


def _purchase_to_form_dict(purchase):
    return {
        "date": purchase.date.strftime("%Y-%m-%d"),
        "supplier_name": purchase.supplier.name,
        "supplier_phone": purchase.supplier.phone,
        "supplier_address": purchase.supplier.address,
        "overall_discount": str(purchase.overall_discount),
        "tax": str(purchase.tax),
        "payment_method": purchase.payment_method,
        "cash_amount": str(purchase.cash_amount),
        "notes": purchase.notes or "",
    }


@purchases_bp.route("/<purchase_id>/edit", methods=["GET", "POST"])
@login_required
def edit_purchase(purchase_id):
    purchase = Purchase.query.get_or_404(purchase_id)

    has_returns = PurchaseReturn.query.filter_by(purchase_id=purchase_id, is_deleted=False).count() > 0
    if has_returns:
        flash("This purchase has returns recorded against it and can't be edited. Delete the return(s) first.", "error")
        return redirect(url_for("purchases.list_purchases"))

    products = Product.query.filter_by(is_active=True).order_by(Product.name).all()

    if request.method == "GET":
        form = _purchase_to_form_dict(purchase)
        existing_items = [
            {
                "product_id": i.product_id,
                "quantity_boxes": str(i.quantity_boxes),
                "purchase_price_per_box": str(i.purchase_price_per_box),
                "sale_price_per_box": str(i.sale_price_per_box),
                "discount": str(i.discount),
            }
            for i in purchase.items
        ]
        return render_template(
            "purchases/form.html",
            products=products,
            products_json=_products_json(products),
            errors=[],
            form=form,
            editing=purchase,
            existing_items_json=json.dumps(existing_items),
        )

    # POST
    errors = []
    date_str = request.form.get("date", "")
    supplier_name = request.form.get("supplier_name", "").strip()
    supplier_phone = request.form.get("supplier_phone", "").strip()
    supplier_address = request.form.get("supplier_address", "").strip()

    product_ids = request.form.getlist("product_id[]")
    quantity_boxes = request.form.getlist("quantity_boxes[]")
    purchase_prices = request.form.getlist("purchase_price_per_box[]")
    sale_prices = request.form.getlist("sale_price_per_box[]")
    discounts = request.form.getlist("discount[]")

    overall_discount = request.form.get("overall_discount", "0")
    tax = request.form.get("tax", "0")
    payment_method = request.form.get("payment_method", "CASH")
    cash_amount = request.form.get("cash_amount", "0")
    notes = request.form.get("notes", "").strip()

    if not date_str:
        errors.append("Date is required.")
    elif _is_future(date_str):
        errors.append("Future dates are not allowed.")
    if not supplier_name or not supplier_phone or not supplier_address:
        errors.append("Supplier name, phone, and address are required.")
    if not product_ids or any(not pid for pid in product_ids):
        errors.append("Select a product for every line.")

    def refetch_and_render():
        return render_template(
            "purchases/form.html",
            products=products,
            products_json=_products_json(products),
            errors=errors,
            form=request.form,
            editing=purchase,
        )

    if errors:
        return refetch_and_render()

    try:
        with db.session.begin_nested():
            supplier = find_or_create_supplier(supplier_name, supplier_phone, supplier_address)

            # Remove old items and cash-ledger entry first, so the
            # negative-stock check below reflects everything else in the
            # system EXCEPT this purchase.
            old_product_ids = {i.product_id for i in purchase.items}
            PurchaseItem.query.filter_by(purchase_id=purchase.id).delete()
            Transaction.query.filter_by(purchase_id=purchase.id).delete()
            db.session.flush()

            prepared_items = []
            for i in range(len(product_ids)):
                product = Product.query.get(product_ids[i])
                if not product:
                    raise ValueError("One of the selected products no longer exists.")

                qty_boxes = float(quantity_boxes[i] or 0)
                purchase_price_box = float(purchase_prices[i] or 0)
                sale_price_box = float(sale_prices[i] or 0)
                discount = float(discounts[i] or 0)

                if qty_boxes <= 0:
                    raise ValueError("Every line needs a quantity greater than 0.")

                packs_per_box = product.packs_per_box
                purchase_pack = round2(purchase_price_box / packs_per_box)
                sale_pack = round2(sale_price_box / packs_per_box)
                product.purchase_price_per_box = purchase_price_box
                product.purchase_price_per_pack = purchase_pack
                product.sale_price_per_box = sale_price_box
                product.sale_price_per_pack = sale_pack

                quantity_packs = round(qty_boxes * packs_per_box)
                line_total = round2(purchase_price_box * qty_boxes - discount)
                if line_total < 0:
                    raise ValueError("A line discount can't exceed that line's total.")

                prepared_items.append(
                    dict(
                        product_id=product.id,
                        packs_per_box_snapshot=packs_per_box,
                        quantity_boxes=qty_boxes,
                        quantity_packs=quantity_packs,
                        purchase_price_per_box=purchase_price_box,
                        purchase_price_per_pack=purchase_pack,
                        sale_price_per_box=sale_price_box,
                        sale_price_per_pack=sale_pack,
                        discount=discount,
                        lineTotal=line_total,
                    )
                )

            # Negative-stock guard: with this purchase's old contribution
            # already removed, adding the new quantities back must not
            # leave any touched product below zero (which would mean stock
            # already sold elsewhere depended on the quantity being reduced).
            touched_ids = old_product_ids | {i["product_id"] for i in prepared_items}
            baseline = get_stock_map(list(touched_ids))
            added_back = {}
            for i in prepared_items:
                added_back[i["product_id"]] = added_back.get(i["product_id"], 0) + i["quantity_packs"]
            for pid in touched_ids:
                resulting = baseline.get(pid, 0) + added_back.get(pid, 0)
                if resulting < 0:
                    product_name = next((p.name for p in products if p.id == pid), "a product")
                    raise ValueError(
                        f"Can't reduce this purchase — {product_name} has already been sold below the new quantity."
                    )

            subtotal = round2(sum(i["lineTotal"] for i in prepared_items))
            grand_total = round2(subtotal - float(overall_discount or 0) + float(tax or 0))
            if grand_total < 0:
                raise ValueError("Overall discount can't exceed the subtotal plus tax.")

            payment = resolve_payment(grand_total, payment_method, float(cash_amount or 0))
            if payment.error:
                raise ValueError(payment.error)

            previous_snapshot = {"grand_total": str(purchase.grand_total), "supplier_id": purchase.supplier_id}

            purchase.date = datetime.strptime(date_str, "%Y-%m-%d")
            purchase.supplier_id = supplier.id
            purchase.subtotal = subtotal
            purchase.overall_discount = float(overall_discount or 0)
            purchase.tax = float(tax or 0)
            purchase.grand_total = grand_total
            purchase.cash_amount = payment.cash_amount
            purchase.credit_amount = payment.credit_amount
            purchase.payment_method = payment_method
            purchase.payment_status = payment.payment_status
            purchase.notes = notes or None
            purchase.updated_at = datetime.utcnow()

            for item in prepared_items:
                line_total = item.pop("lineTotal")
                db.session.add(PurchaseItem(purchase_id=purchase.id, line_total=line_total, **item))

            if payment.cash_amount > 0:
                db.session.add(
                    Transaction(
                        date=purchase.date,
                        type="CASH_OUT",
                        category="PURCHASE",
                        description=f"Purchase {purchase.invoice_number} \u2014 {supplier.name}",
                        amount=payment.cash_amount,
                        purchase_id=purchase.id,
                    )
                )

            db.session.add(
                AuditLog(
                    user_id=current_user.id,
                    action="UPDATE",
                    record_type="Purchase",
                    record_id=purchase.id,
                    previous_value=previous_snapshot,
                    new_value={"grand_total": str(grand_total), "supplier_id": supplier.id},
                )
            )

        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        errors.append(str(e))
        return refetch_and_render()

    flash(f"Purchase {purchase.invoice_number} updated.", "success")
    return redirect(url_for("purchases.list_purchases"))


@purchases_bp.route("/<purchase_id>/delete", methods=["POST"])
@login_required
def delete_purchase(purchase_id):
    purchase = Purchase.query.get_or_404(purchase_id)

    has_returns = PurchaseReturn.query.filter_by(purchase_id=purchase_id, is_deleted=False).count() > 0
    if has_returns:
        flash("This purchase has returns recorded against it and can't be deleted.", "error")
        return redirect(url_for("purchases.list_purchases"))

    product_ids = [i.product_id for i in purchase.items]

    try:
        with db.session.begin_nested():
            previous_snapshot = {"invoice_number": purchase.invoice_number, "grand_total": str(purchase.grand_total)}
            purchase.is_deleted = True
            purchase.updated_at = datetime.utcnow()
            Transaction.query.filter_by(purchase_id=purchase.id).delete()
            db.session.flush()

            stock_after = get_stock_map(product_ids)
            negative = [pid for pid in product_ids if stock_after.get(pid, 0) < 0]
            if negative:
                product = Product.query.get(negative[0])
                raise ValueError(
                    f"Can't delete this purchase — {product.name if product else 'a product'} has already been sold and would go negative in stock."
                )

            db.session.add(
                AuditLog(user_id=current_user.id, action="DELETE", record_type="Purchase", record_id=purchase.id, previous_value=previous_snapshot)
            )

        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        flash(str(e), "error")
        return redirect(url_for("purchases.list_purchases"))

    flash(f"Purchase {purchase.invoice_number} deleted. Its invoice number will never be reused.", "success")
    return redirect(url_for("purchases.list_purchases"))
