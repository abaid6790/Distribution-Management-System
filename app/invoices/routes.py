from flask import Blueprint, render_template, request
from flask_login import login_required

from app.extensions import db
from app.models import (
    Sale,
    Purchase,
    SaleReturn,
    PurchaseReturn,
    CustomerPayment,
    SupplierPayment,
    Customer,
    Supplier,
    Employee,
    BusinessSettings,
    PrintingSettings,
)

invoices_bp = Blueprint("invoices", __name__, url_prefix="/invoices")


def _get_settings():
    business = BusinessSettings.query.get("singleton") or BusinessSettings(id="singleton")
    printing = PrintingSettings.query.get("singleton") or PrintingSettings(id="singleton")
    return business, printing


@invoices_bp.route("/")
@login_required
def index():
    q = request.args.get("q", "").strip()
    type_filter = request.args.get("type", "")

    rows = []

    if not type_filter or type_filter == "sale":
        query = db.session.query(Sale, Customer).join(Customer, Sale.customer_id == Customer.id).filter(Sale.is_deleted.is_(False))
        if q:
            like = f"%{q}%"
            query = query.filter(db.or_(Sale.invoice_number.ilike(like), Customer.name.ilike(like)))
        for s, c in query.all():
            rows.append({"number": s.invoice_number, "date": s.date, "type": "Sale", "party": c.name, "amount": s.grand_total, "status": s.payment_status, "id": s.id})

    if not type_filter or type_filter == "purchase":
        query = db.session.query(Purchase, Supplier).join(Supplier, Purchase.supplier_id == Supplier.id).filter(Purchase.is_deleted.is_(False))
        if q:
            like = f"%{q}%"
            query = query.filter(db.or_(Purchase.invoice_number.ilike(like), Supplier.name.ilike(like)))
        for p, s in query.all():
            rows.append({"number": p.invoice_number, "date": p.date, "type": "Purchase", "party": s.name, "amount": p.grand_total, "status": p.payment_status, "id": p.id})

    if not type_filter or type_filter == "sale_return":
        query = db.session.query(SaleReturn, Customer).join(Customer, SaleReturn.customer_id == Customer.id).filter(SaleReturn.is_deleted.is_(False))
        if q:
            like = f"%{q}%"
            query = query.filter(db.or_(SaleReturn.return_invoice_number.ilike(like), Customer.name.ilike(like)))
        for r, c in query.all():
            rows.append({"number": r.return_invoice_number, "date": r.date, "type": "Sale Return", "party": c.name, "amount": r.grand_total, "status": None, "id": r.id})

    if not type_filter or type_filter == "purchase_return":
        query = db.session.query(PurchaseReturn, Supplier).join(Supplier, PurchaseReturn.supplier_id == Supplier.id).filter(PurchaseReturn.is_deleted.is_(False))
        if q:
            like = f"%{q}%"
            query = query.filter(db.or_(PurchaseReturn.return_invoice_number.ilike(like), Supplier.name.ilike(like)))
        for r, s in query.all():
            rows.append({"number": r.return_invoice_number, "date": r.date, "type": "Purchase Return", "party": s.name, "amount": r.grand_total, "status": None, "id": r.id})

    if not type_filter or type_filter == "customer_payment":
        query = db.session.query(CustomerPayment, Customer).join(Customer, CustomerPayment.customer_id == Customer.id)
        if q:
            like = f"%{q}%"
            query = query.filter(Customer.name.ilike(like))
        for pay, c in query.all():
            rows.append({"number": f"RCPT-{pay.id[:8].upper()}", "date": pay.date, "type": "Customer Receipt", "party": c.name, "amount": pay.amount, "status": None, "id": pay.id})

    if not type_filter or type_filter == "supplier_payment":
        query = db.session.query(SupplierPayment, Supplier).join(Supplier, SupplierPayment.supplier_id == Supplier.id)
        if q:
            like = f"%{q}%"
            query = query.filter(Supplier.name.ilike(like))
        for pay, s in query.all():
            rows.append({"number": f"RCPT-{pay.id[:8].upper()}", "date": pay.date, "type": "Supplier Receipt", "party": s.name, "amount": pay.amount, "status": None, "id": pay.id})

    rows.sort(key=lambda r: r["date"], reverse=True)

    return render_template("invoices/list.html", rows=rows, q=q, type_filter=type_filter)


@invoices_bp.route("/sale/<sale_id>/print")
@login_required
def print_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    business, printing = _get_settings()
    return render_template("invoices/print_sale.html", sale=sale, business=business, printing=printing)


@invoices_bp.route("/purchase/<purchase_id>/print")
@login_required
def print_purchase(purchase_id):
    purchase = Purchase.query.get_or_404(purchase_id)
    business, printing = _get_settings()
    return render_template("invoices/print_purchase.html", purchase=purchase, business=business, printing=printing)


@invoices_bp.route("/sale-return/<return_id>/print")
@login_required
def print_sale_return(return_id):
    sale_return = SaleReturn.query.get_or_404(return_id)
    business, printing = _get_settings()
    return render_template("invoices/print_sale_return.html", r=sale_return, business=business, printing=printing)


@invoices_bp.route("/purchase-return/<return_id>/print")
@login_required
def print_purchase_return(return_id):
    purchase_return = PurchaseReturn.query.get_or_404(return_id)
    business, printing = _get_settings()
    return render_template("invoices/print_purchase_return.html", r=purchase_return, business=business, printing=printing)


@invoices_bp.route("/customer-payment/<payment_id>/print")
@login_required
def print_customer_payment(payment_id):
    payment = CustomerPayment.query.get_or_404(payment_id)
    business, printing = _get_settings()
    return render_template("invoices/print_payment.html", payment=payment, party=payment.customer, direction="Received from", business=business, printing=printing)


@invoices_bp.route("/supplier-payment/<payment_id>/print")
@login_required
def print_supplier_payment(payment_id):
    payment = SupplierPayment.query.get_or_404(payment_id)
    business, printing = _get_settings()
    return render_template("invoices/print_payment.html", payment=payment, party=payment.supplier, direction="Paid to", business=business, printing=printing)
