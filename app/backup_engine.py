from datetime import datetime, date
from decimal import Decimal

from app.extensions import db
from app.models import (
    Employee,
    User,
    Product,
    Customer,
    Supplier,
    Sale,
    SaleItem,
    Purchase,
    PurchaseItem,
    SaleReturn,
    SaleReturnItem,
    PurchaseReturn,
    PurchaseReturnItem,
    StockAdjustment,
    OpeningStock,
    OpeningDebtor,
    OpeningCreditor,
    CustomerPayment,
    SupplierPayment,
    Expense,
    Transaction,
    AuditLog,
    BusinessSettings,
    InvoiceSettings,
    PrintingSettings,
    Backup,
)

# Parent-first order: safe for INSERT during restore. Reversed, it's safe
# for DELETE during wipe/reset (children removed before their parents).
ALL_TABLES = [
    ("employees", Employee),
    ("users", User),
    ("products", Product),
    ("customers", Customer),
    ("suppliers", Supplier),
    ("sales", Sale),
    ("sale_items", SaleItem),
    ("purchases", Purchase),
    ("purchase_items", PurchaseItem),
    ("sale_returns", SaleReturn),
    ("sale_return_items", SaleReturnItem),
    ("purchase_returns", PurchaseReturn),
    ("purchase_return_items", PurchaseReturnItem),
    ("stock_adjustments", StockAdjustment),
    ("opening_stock", OpeningStock),
    ("opening_debtors", OpeningDebtor),
    ("opening_creditors", OpeningCreditor),
    ("customer_payments", CustomerPayment),
    ("supplier_payments", SupplierPayment),
    ("expenses", Expense),
    ("transactions", Transaction),
    ("audit_logs", AuditLog),
    ("business_settings", BusinessSettings),
    ("invoice_settings", InvoiceSettings),
    ("printing_settings", PrintingSettings),
]

# Tables touched by the Danger Zone reset. Deliberately excludes User
# accounts, all *Settings tables, and AuditLog — resetting business data
# shouldn't lock the admin out or erase the record that a reset happened.
RESET_TABLES = [
    ("transactions", Transaction),
    ("sale_return_items", SaleReturnItem),
    ("sale_returns", SaleReturn),
    ("purchase_return_items", PurchaseReturnItem),
    ("purchase_returns", PurchaseReturn),
    ("sale_items", SaleItem),
    ("sales", Sale),
    ("purchase_items", PurchaseItem),
    ("purchases", Purchase),
    ("stock_adjustments", StockAdjustment),
    ("opening_stock", OpeningStock),
    ("opening_debtors", OpeningDebtor),
    ("opening_creditors", OpeningCreditor),
    ("customer_payments", CustomerPayment),
    ("supplier_payments", SupplierPayment),
    ("expenses", Expense),
    ("customers", Customer),
    ("suppliers", Supplier),
    ("products", Product),
    ("employees", Employee),
]


def _serialize_value(v):
    if isinstance(v, Decimal):
        return str(v)
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    return v


def _deserialize_value(column, v):
    if v is None:
        return None
    col_type = column.type.__class__.__name__
    if col_type == "DateTime" and isinstance(v, str):
        return datetime.fromisoformat(v)
    return v


def dump_all():
    """Returns a JSON-serializable dict: {table_name: [row_dict, ...]}."""
    data = {}
    for name, model in ALL_TABLES:
        rows = model.query.all()
        cols = model.__table__.columns
        data[name] = [{c.name: _serialize_value(getattr(row, c.name)) for c in cols} for row in rows]
    return data


def restore_all(data: dict):
    """Wipes every table in ALL_TABLES and reinserts from `data`, in
    dependency-safe order, inside a single transaction."""
    # Backup history rows reference users.id but aren't themselves part of
    # the dump/restore payload — clear them first so wiping Users below
    # doesn't hit a foreign-key violation. (Old backup files still exist on
    # disk; only the in-app history list is cleared.)
    db.session.query(Backup).delete()
    db.session.flush()

    for name, model in reversed(ALL_TABLES):
        db.session.query(model).delete()
    db.session.flush()

    for name, model in ALL_TABLES:
        rows = data.get(name, [])
        cols = model.__table__.columns
        for row_dict in rows:
            kwargs = {c.name: _deserialize_value(c, row_dict.get(c.name)) for c in cols}
            db.session.add(model(**kwargs))
        db.session.flush()


def reset_business_data():
    """Danger Zone: wipes business data, keeps users/settings/audit log."""
    # Employees are referenced by users.employee_id — detach before delete.
    db.session.query(User).update({User.employee_id: None})
    db.session.flush()

    for name, model in RESET_TABLES:
        db.session.query(model).delete()
    db.session.flush()
