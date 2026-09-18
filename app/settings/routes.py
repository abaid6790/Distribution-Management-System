from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.extensions import db
from app.models import BusinessSettings, InvoiceSettings, PrintingSettings, AuditLog

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


def _get_or_create(model):
    row = model.query.get("singleton")
    if not row:
        row = model(id="singleton")
        db.session.add(row)
        db.session.commit()
    return row


@settings_bp.route("/")
@login_required
def index():
    tab = request.args.get("tab", "business")
    business = _get_or_create(BusinessSettings)
    invoice = _get_or_create(InvoiceSettings)
    printing = _get_or_create(PrintingSettings)
    return render_template("settings/index.html", tab=tab, business=business, invoice=invoice, printing=printing, errors=[])


@settings_bp.route("/business", methods=["POST"])
@login_required
def update_business():
    business = _get_or_create(BusinessSettings)
    name = request.form.get("business_name", "").strip()
    errors = []
    if not name:
        errors.append("Business name is required.")

    if errors:
        invoice = _get_or_create(InvoiceSettings)
        printing = _get_or_create(PrintingSettings)
        return render_template("settings/index.html", tab="business", business=business, invoice=invoice, printing=printing, errors=errors)

    before = {"business_name": business.business_name}
    business.business_name = name
    business.address = request.form.get("address", "").strip() or None
    business.phone = request.form.get("phone", "").strip() or None
    business.email = request.form.get("email", "").strip() or None
    business.tax_number = request.form.get("tax_number", "").strip() or None

    db.session.add(AuditLog(user_id=current_user.id, action="SETTINGS_CHANGE", record_type="BusinessSettings", record_id="singleton", previous_value=before))
    db.session.commit()
    flash("Business settings saved.", "success")
    return redirect(url_for("settings.index", tab="business"))


@settings_bp.route("/invoice", methods=["POST"])
@login_required
def update_invoice():
    invoice = _get_or_create(InvoiceSettings)
    errors = []

    padding = request.form.get("number_padding", "6").strip()
    try:
        padding = int(padding)
        if padding < 1 or padding > 12:
            errors.append("Number padding must be between 1 and 12.")
    except ValueError:
        errors.append("Number padding must be a whole number.")
        padding = 6

    for field in ["sale_prefix", "purchase_prefix", "sale_return_prefix", "purchase_return_prefix", "payment_receipt_prefix"]:
        if not request.form.get(field, "").strip():
            errors.append("All invoice prefixes are required.")
            break

    if errors:
        business = _get_or_create(BusinessSettings)
        printing = _get_or_create(PrintingSettings)
        return render_template("settings/index.html", tab="invoice", business=business, invoice=invoice, printing=printing, errors=errors)

    invoice.sale_prefix = request.form.get("sale_prefix", "").strip()
    invoice.purchase_prefix = request.form.get("purchase_prefix", "").strip()
    invoice.sale_return_prefix = request.form.get("sale_return_prefix", "").strip()
    invoice.purchase_return_prefix = request.form.get("purchase_return_prefix", "").strip()
    invoice.payment_receipt_prefix = request.form.get("payment_receipt_prefix", "").strip()
    invoice.number_padding = padding
    invoice.invoice_footer = request.form.get("invoice_footer", "").strip() or None
    invoice.default_notes = request.form.get("default_notes", "").strip() or None

    db.session.add(AuditLog(user_id=current_user.id, action="SETTINGS_CHANGE", record_type="InvoiceSettings", record_id="singleton"))
    db.session.commit()
    flash("Invoice numbering saved. This only affects invoices created from now on.", "success")
    return redirect(url_for("settings.index", tab="invoice"))


@settings_bp.route("/printing", methods=["POST"])
@login_required
def update_printing():
    printing = _get_or_create(PrintingSettings)

    printing.paper_size = request.form.get("paper_size", "A4")
    printing.show_logo = request.form.get("show_logo") == "on"
    printing.show_business_info = request.form.get("show_business_info") == "on"
    printing.show_customer_info = request.form.get("show_customer_info") == "on"
    try:
        printing.margin_mm = int(request.form.get("margin_mm", 10))
    except ValueError:
        printing.margin_mm = 10
    printing.footer_text = request.form.get("footer_text", "").strip() or None

    db.session.add(AuditLog(user_id=current_user.id, action="SETTINGS_CHANGE", record_type="PrintingSettings", record_id="singleton"))
    db.session.commit()
    flash("Printing settings saved.", "success")
    return redirect(url_for("settings.index", tab="printing"))
