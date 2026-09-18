"""
Atomically reserves and returns the next invoice number for the given type.
Uses SELECT ... FOR UPDATE to lock the settings row for the duration of the
enclosing transaction, so two simultaneous requests can never receive the
same invoice number and numbers are never skipped-then-reused.
"""

from app.extensions import db
from app.models import InvoiceSettings

COUNTER_FIELD = {
    "sale": "next_sale_number",
    "purchase": "next_purchase_number",
    "sale_return": "next_sale_return_number",
    "purchase_return": "next_purchase_return_number",
    "receipt": "next_receipt_number",
}

PREFIX_FIELD = {
    "sale": "sale_prefix",
    "purchase": "purchase_prefix",
    "sale_return": "sale_return_prefix",
    "purchase_return": "purchase_return_prefix",
    "receipt": "payment_receipt_prefix",
}


def generate_invoice_number(invoice_type: str) -> str:
    settings = (
        db.session.query(InvoiceSettings)
        .filter(InvoiceSettings.id == "singleton")
        .with_for_update()
        .one()
    )

    counter_field = COUNTER_FIELD[invoice_type]
    prefix_field = PREFIX_FIELD[invoice_type]

    current_number = getattr(settings, counter_field)
    prefix = getattr(settings, prefix_field)

    setattr(settings, counter_field, current_number + 1)
    db.session.add(settings)

    return f"{prefix}{str(current_number).zfill(settings.number_padding)}"
