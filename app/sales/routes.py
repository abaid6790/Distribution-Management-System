import json
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import or_

from app.extensions import db
from app.models import Sale, SaleItem, Product, Customer, Employee, Transaction, AuditLog, SaleReturn
from app.parties import find_or_create_customer
from app.invoice_numbers import generate_invoice_number
from app.payments import resolve_payment, round2
from app.stock import get_stock_map

sales_bp = Blueprint("sales", __name__, url_prefix="/sales")


def _is_future(date_str):
    d = datetime.strptime(date_str, "%Y-%m-%d").date()
    return d > datetime.now().date()


def _products_json(products, stock_map):
    return json.dumps(
        [
            {
                "id": p.id,
                "name": p.name,
                "sku": p.sku,
                "packs_per_box": p.packs_per_box,
                "sale_price_per_box": float(p.sale_price_per_box),
                "sale_price_per_pack": float(p.sale_price_per_pack),
                "current_stock_packs": int(stock_map.get(p.id, 0)),
            }
            for p in products
        ]
    )


@sales_bp.route("/")
@login_required
def list_sales():
    q = request.args.get("q", "").strip()
    query = (
        Sale.query.join(Customer, Sale.customer_id == Customer.id)
        .join(Employee, Sale.booked_by_id == Employee.id)
        .filter(Sale.is_deleted.is_(False))
    )
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Sale.invoice_number.ilike(like), Customer.name.ilike(like), Customer.phone.ilike(like)))
    rows = query.order_by(Sale.created_at.desc()).all()
    return render_template("sales/list.html", rows=rows, q=q)


@sales_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_sale():
    products = Product.query.filter_by(is_active=True).order_by(Product.name).all()
    stock_map = get_stock_map([p.id for p in products])
    employees = Employee.query.filter_by(is_active=True).order_by(Employee.name).all()

    if request.method == "POST":
        errors = []
        date_str = request.form.get("date", "")
        customer_name = request.form.get("customer_name", "").strip()
        customer_phone = request.form.get("customer_phone", "").strip()
        customer_address = request.form.get("customer_address", "").strip()
        booked_by_id = request.form.get("booked_by_id", "").strip()

        product_ids = request.form.getlist("product_id[]")
        unit_types = request.form.getlist("unit_type[]")
        quantities = request.form.getlist("quantity[]")
        unit_prices = request.form.getlist("unit_price[]")
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
        if not customer_name or not customer_phone or not customer_address:
            errors.append("Customer name, phone, and address are required.")
        if not booked_by_id:
            errors.append('Select who booked this sale.')
        if not product_ids or any(not pid for pid in product_ids):
            errors.append("Select a product for every line.")

        def refetch_and_render():
            return render_template(
                "sales/form.html",
                products=products,
                products_json=_products_json(products, stock_map),
                employees=employees,
                errors=errors,
                form=request.form,
            )

        if errors:
            return refetch_and_render()

        try:
            with db.session.begin_nested():
                employee = Employee.query.get(booked_by_id)
                if not employee:
                    raise ValueError('Select a valid employee for "Booked By."')

                customer = find_or_create_customer(customer_name, customer_phone, customer_address)

                product_map = {}
                for pid in set(product_ids):
                    product = Product.query.get(pid)
                    if not product:
                        raise ValueError("One of the selected products no longer exists.")
                    product_map[pid] = product

                live_stock = get_stock_map(list(product_map.keys()))

                prepared_items = []
                requested_packs_by_product = {}

                for i in range(len(product_ids)):
                    product = product_map[product_ids[i]]
                    unit_type = unit_types[i]
                    quantity = float(quantities[i] or 0)
                    unit_price = float(unit_prices[i] or 0)
                    discount = float(discounts[i] or 0)

                    if quantity <= 0:
                        raise ValueError("Every line needs a quantity greater than 0.")

                    quantity_packs = round(quantity * product.packs_per_box) if unit_type == "BOX" else round(quantity)
                    requested_packs_by_product[product.id] = requested_packs_by_product.get(product.id, 0) + quantity_packs

                    line_total = round2(unit_price * quantity - discount)
                    if line_total < 0:
                        raise ValueError("A line discount can't exceed that line's total.")

                    prepared_items.append(
                        dict(
                            product_id=product.id,
                            unit_type=unit_type,
                            quantity=quantity,
                            quantity_packs=quantity_packs,
                            unit_price=unit_price,
                            discount=discount,
                            line_total=line_total,
                        )
                    )

                for product_id, requested in requested_packs_by_product.items():
                    available = live_stock.get(product_id, 0)
                    if requested > available:
                        raise ValueError(
                            f"Insufficient stock for {product_map[product_id].name}. Available quantity: {int(available)} packs."
                        )

                subtotal = round2(sum(i["line_total"] for i in prepared_items))
                grand_total = round2(subtotal - float(overall_discount or 0) + float(tax or 0))
                if grand_total < 0:
                    raise ValueError("Overall discount can't exceed the subtotal plus tax.")

                payment = resolve_payment(grand_total, payment_method, float(cash_amount or 0))
                if payment.error:
                    raise ValueError(payment.error)

                invoice_number = generate_invoice_number("sale")

                sale = Sale(
                    invoice_number=invoice_number,
                    date=datetime.strptime(date_str, "%Y-%m-%d"),
                    customer_id=customer.id,
                    booked_by_id=employee.id,
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
                db.session.add(sale)
                db.session.flush()

                for item in prepared_items:
                    db.session.add(SaleItem(sale_id=sale.id, **item))

                if payment.cash_amount > 0:
                    db.session.add(
                        Transaction(
                            date=sale.date,
                            type="CASH_IN",
                            category="SALE",
                            description=f"Sale {invoice_number} \u2014 {customer.name}",
                            amount=payment.cash_amount,
                            sale_id=sale.id,
                        )
                    )

                db.session.add(AuditLog(user_id=current_user.id, action="CREATE", record_type="Sale", record_id=sale.id))

            db.session.commit()
        except ValueError as e:
            db.session.rollback()
            errors.append(str(e))
            return refetch_and_render()

        flash(f"Sale {invoice_number} created.", "success")
        return redirect(url_for("sales.list_sales"))

    return render_template(
        "sales/form.html",
        products=products,
        products_json=_products_json(products, stock_map),
        employees=employees,
        errors=[],
        form={},
    )


def _sale_to_form_dict(sale):
    return {
        "date": sale.date.strftime("%Y-%m-%d"),
        "customer_name": sale.customer.name,
        "customer_phone": sale.customer.phone,
        "customer_address": sale.customer.address,
        "booked_by_id": sale.booked_by_id,
        "overall_discount": str(sale.overall_discount),
        "tax": str(sale.tax),
        "payment_method": sale.payment_method,
        "cash_amount": str(sale.cash_amount),
        "notes": sale.notes or "",
    }


@sales_bp.route("/<sale_id>/edit", methods=["GET", "POST"])
@login_required
def edit_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)

    has_returns = SaleReturn.query.filter_by(sale_id=sale_id, is_deleted=False).count() > 0
    if has_returns:
        flash("This sale has returns recorded against it and can't be edited. Delete the return(s) first.", "error")
        return redirect(url_for("sales.list_sales"))

    products = Product.query.filter_by(is_active=True).order_by(Product.name).all()
    # Include this sale's own products even if since deactivated, and its
    # own quantity should NOT count against itself in the stock check.
    stock_map = get_stock_map([p.id for p in products])
    for item in sale.items:
        stock_map[item.product_id] = stock_map.get(item.product_id, 0) + item.quantity_packs
    employees = Employee.query.filter_by(is_active=True).order_by(Employee.name).all()

    if request.method == "GET":
        form = _sale_to_form_dict(sale)
        existing_items = [
            {
                "product_id": i.product_id,
                "unit_type": i.unit_type,
                "quantity": str(i.quantity),
                "unit_price": str(i.unit_price),
                "discount": str(i.discount),
            }
            for i in sale.items
        ]
        return render_template(
            "sales/form.html",
            products=products,
            products_json=_products_json(products, stock_map),
            employees=employees,
            errors=[],
            form=form,
            editing=sale,
            existing_items_json=json.dumps(existing_items),
        )

    # POST
    errors = []
    date_str = request.form.get("date", "")
    customer_name = request.form.get("customer_name", "").strip()
    customer_phone = request.form.get("customer_phone", "").strip()
    customer_address = request.form.get("customer_address", "").strip()
    booked_by_id = request.form.get("booked_by_id", "").strip()

    product_ids = request.form.getlist("product_id[]")
    unit_types = request.form.getlist("unit_type[]")
    quantities = request.form.getlist("quantity[]")
    unit_prices = request.form.getlist("unit_price[]")
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
    if not customer_name or not customer_phone or not customer_address:
        errors.append("Customer name, phone, and address are required.")
    if not booked_by_id:
        errors.append('Select who booked this sale.')
    if not product_ids or any(not pid for pid in product_ids):
        errors.append("Select a product for every line.")

    def refetch_and_render():
        return render_template(
            "sales/form.html",
            products=products,
            products_json=_products_json(products, stock_map),
            employees=employees,
            errors=errors,
            form=request.form,
            editing=sale,
        )

    if errors:
        return refetch_and_render()

    try:
        with db.session.begin_nested():
            employee = Employee.query.get(booked_by_id)
            if not employee:
                raise ValueError('Select a valid employee for "Booked By."')

            customer = find_or_create_customer(customer_name, customer_phone, customer_address)

            # Remove the old line items and cash-ledger entry FIRST so the
            # stock check below sees a clean slate, then re-validates the
            # new quantities against real availability.
            SaleItem.query.filter_by(sale_id=sale.id).delete()
            Transaction.query.filter_by(sale_id=sale.id).delete()
            db.session.flush()

            product_map = {}
            for pid in set(product_ids):
                product = Product.query.get(pid)
                if not product:
                    raise ValueError("One of the selected products no longer exists.")
                product_map[pid] = product

            live_stock = get_stock_map(list(product_map.keys()))

            prepared_items = []
            requested_packs_by_product = {}

            for i in range(len(product_ids)):
                product = product_map[product_ids[i]]
                unit_type = unit_types[i]
                quantity = float(quantities[i] or 0)
                unit_price = float(unit_prices[i] or 0)
                discount = float(discounts[i] or 0)

                if quantity <= 0:
                    raise ValueError("Every line needs a quantity greater than 0.")

                quantity_packs = round(quantity * product.packs_per_box) if unit_type == "BOX" else round(quantity)
                requested_packs_by_product[product.id] = requested_packs_by_product.get(product.id, 0) + quantity_packs

                line_total = round2(unit_price * quantity - discount)
                if line_total < 0:
                    raise ValueError("A line discount can't exceed that line's total.")

                prepared_items.append(
                    dict(
                        product_id=product.id,
                        unit_type=unit_type,
                        quantity=quantity,
                        quantity_packs=quantity_packs,
                        unit_price=unit_price,
                        discount=discount,
                        line_total=line_total,
                    )
                )

            for product_id, requested in requested_packs_by_product.items():
                available = live_stock.get(product_id, 0)
                if requested > available:
                    raise ValueError(
                        f"Insufficient stock for {product_map[product_id].name}. Available quantity: {int(available)} packs."
                    )

            subtotal = round2(sum(i["line_total"] for i in prepared_items))
            grand_total = round2(subtotal - float(overall_discount or 0) + float(tax or 0))
            if grand_total < 0:
                raise ValueError("Overall discount can't exceed the subtotal plus tax.")

            payment = resolve_payment(grand_total, payment_method, float(cash_amount or 0))
            if payment.error:
                raise ValueError(payment.error)

            previous_snapshot = {
                "grand_total": str(sale.grand_total),
                "customer_id": sale.customer_id,
                "payment_status": sale.payment_status,
            }

            sale.date = datetime.strptime(date_str, "%Y-%m-%d")
            sale.customer_id = customer.id
            sale.booked_by_id = employee.id
            sale.subtotal = subtotal
            sale.overall_discount = float(overall_discount or 0)
            sale.tax = float(tax or 0)
            sale.grand_total = grand_total
            sale.cash_amount = payment.cash_amount
            sale.credit_amount = payment.credit_amount
            sale.payment_method = payment_method
            sale.payment_status = payment.payment_status
            sale.notes = notes or None
            sale.updated_at = datetime.utcnow()

            for item in prepared_items:
                db.session.add(SaleItem(sale_id=sale.id, **item))

            if payment.cash_amount > 0:
                db.session.add(
                    Transaction(
                        date=sale.date,
                        type="CASH_IN",
                        category="SALE",
                        description=f"Sale {sale.invoice_number} \u2014 {customer.name}",
                        amount=payment.cash_amount,
                        sale_id=sale.id,
                    )
                )

            db.session.add(
                AuditLog(
                    user_id=current_user.id,
                    action="UPDATE",
                    record_type="Sale",
                    record_id=sale.id,
                    previous_value=previous_snapshot,
                    new_value={"grand_total": str(grand_total), "customer_id": customer.id, "payment_status": payment.payment_status},
                )
            )

        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        errors.append(str(e))
        return refetch_and_render()

    flash(f"Sale {sale.invoice_number} updated.", "success")
    return redirect(url_for("sales.list_sales"))


@sales_bp.route("/<sale_id>/delete", methods=["POST"])
@login_required
def delete_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)

    has_returns = SaleReturn.query.filter_by(sale_id=sale_id, is_deleted=False).count() > 0
    if has_returns:
        flash("This sale has returns recorded against it and can't be deleted.", "error")
        return redirect(url_for("sales.list_sales"))

    previous_snapshot = {"invoice_number": sale.invoice_number, "grand_total": str(sale.grand_total)}

    sale.is_deleted = True
    sale.updated_at = datetime.utcnow()
    Transaction.query.filter_by(sale_id=sale.id).delete()

    db.session.add(
        AuditLog(user_id=current_user.id, action="DELETE", record_type="Sale", record_id=sale.id, previous_value=previous_snapshot)
    )
    db.session.commit()

    flash(f"Sale {sale.invoice_number} deleted. Its invoice number will never be reused.", "success")
    return redirect(url_for("sales.list_sales"))
