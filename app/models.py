import uuid
from datetime import datetime, timezone

from app.extensions import db


def gen_id():
    return uuid.uuid4().hex


def now():
    return datetime.now(timezone.utc)


class Employee(db.Model):
    __tablename__ = "employees"
    id = db.Column(db.String, primary_key=True, default=gen_id)
    employee_code = db.Column(db.String, unique=True, nullable=False)
    name = db.Column(db.String, nullable=False)
    phone = db.Column(db.String)
    address = db.Column(db.String)
    cnic = db.Column(db.String)
    email = db.Column(db.String)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now, onupdate=now)

    user = db.relationship("User", back_populates="employee", uselist=False)
    sales_booked = db.relationship("Sale", back_populates="booked_by")


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.String, primary_key=True, default=gen_id)
    username = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    full_name = db.Column(db.String, nullable=False)
    role = db.Column(db.String, nullable=False, default="SALESMAN")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    permissions = db.Column(db.JSON, nullable=False, default=list)
    must_change_password = db.Column(db.Boolean, nullable=False, default=False)
    employee_id = db.Column(db.String, db.ForeignKey("employees.id"), unique=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now, onupdate=now)

    employee = db.relationship("Employee", back_populates="user")

    def has_permission(self, module_key: str) -> bool:
        if self.role == "ADMIN":
            return True
        return module_key in (self.permissions or [])

    # Flask-Login required properties
    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id


class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.String, primary_key=True, default=gen_id)
    sku = db.Column(db.String, unique=True, nullable=False)
    name = db.Column(db.String, nullable=False)
    category = db.Column(db.String)
    packs_per_box = db.Column(db.Integer, nullable=False, default=1)
    purchase_price_per_box = db.Column(db.Numeric(14, 2), nullable=False)
    purchase_price_per_pack = db.Column(db.Numeric(14, 2), nullable=False)
    sale_price_per_box = db.Column(db.Numeric(14, 2), nullable=False)
    sale_price_per_pack = db.Column(db.Numeric(14, 2), nullable=False)
    min_stock_level_packs = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now, onupdate=now)


class Customer(db.Model):
    __tablename__ = "customers"
    id = db.Column(db.String, primary_key=True, default=gen_id)
    name = db.Column(db.String, nullable=False)
    phone = db.Column(db.String, nullable=False)
    address = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now, onupdate=now)

    __table_args__ = (db.UniqueConstraint("name", "phone", "address", name="customers_identity_uq"),)


class Supplier(db.Model):
    __tablename__ = "suppliers"
    id = db.Column(db.String, primary_key=True, default=gen_id)
    name = db.Column(db.String, nullable=False)
    phone = db.Column(db.String, nullable=False)
    address = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now, onupdate=now)

    __table_args__ = (db.UniqueConstraint("name", "phone", "address", name="suppliers_identity_uq"),)


class Sale(db.Model):
    __tablename__ = "sales"
    id = db.Column(db.String, primary_key=True, default=gen_id)
    invoice_number = db.Column(db.String, unique=True, nullable=False)
    date = db.Column(db.DateTime(timezone=True), nullable=False)
    customer_id = db.Column(db.String, db.ForeignKey("customers.id"), nullable=False)
    booked_by_id = db.Column(db.String, db.ForeignKey("employees.id"), nullable=False)
    subtotal = db.Column(db.Numeric(14, 2), nullable=False)
    overall_discount = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    tax = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    grand_total = db.Column(db.Numeric(14, 2), nullable=False)
    cash_amount = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    credit_amount = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    payment_method = db.Column(db.String, nullable=False)
    payment_status = db.Column(db.String, nullable=False)
    notes = db.Column(db.String)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    created_by_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now, onupdate=now)

    customer = db.relationship("Customer")
    booked_by = db.relationship("Employee", back_populates="sales_booked")
    items = db.relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")


class SaleItem(db.Model):
    __tablename__ = "sale_items"
    id = db.Column(db.String, primary_key=True, default=gen_id)
    sale_id = db.Column(db.String, db.ForeignKey("sales.id", ondelete="CASCADE"), nullable=False)
    product_id = db.Column(db.String, db.ForeignKey("products.id"), nullable=False)
    unit_type = db.Column(db.String, nullable=False)  # BOX | PACK
    quantity = db.Column(db.Numeric(14, 3), nullable=False)
    quantity_packs = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(14, 2), nullable=False)
    discount = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    line_total = db.Column(db.Numeric(14, 2), nullable=False)

    sale = db.relationship("Sale", back_populates="items")
    product = db.relationship("Product")


class Purchase(db.Model):
    __tablename__ = "purchases"
    id = db.Column(db.String, primary_key=True, default=gen_id)
    invoice_number = db.Column(db.String, unique=True, nullable=False)
    date = db.Column(db.DateTime(timezone=True), nullable=False)
    supplier_id = db.Column(db.String, db.ForeignKey("suppliers.id"), nullable=False)
    subtotal = db.Column(db.Numeric(14, 2), nullable=False)
    overall_discount = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    tax = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    grand_total = db.Column(db.Numeric(14, 2), nullable=False)
    cash_amount = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    credit_amount = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    payment_method = db.Column(db.String, nullable=False)
    payment_status = db.Column(db.String, nullable=False)
    notes = db.Column(db.String)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    created_by_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now, onupdate=now)

    supplier = db.relationship("Supplier")
    items = db.relationship("PurchaseItem", back_populates="purchase", cascade="all, delete-orphan")


class PurchaseItem(db.Model):
    __tablename__ = "purchase_items"
    id = db.Column(db.String, primary_key=True, default=gen_id)
    purchase_id = db.Column(db.String, db.ForeignKey("purchases.id", ondelete="CASCADE"), nullable=False)
    product_id = db.Column(db.String, db.ForeignKey("products.id"), nullable=False)
    quantity_boxes = db.Column(db.Numeric(14, 3), nullable=False)
    packs_per_box_snapshot = db.Column(db.Integer, nullable=False)
    quantity_packs = db.Column(db.Integer, nullable=False)
    purchase_price_per_box = db.Column(db.Numeric(14, 2), nullable=False)
    purchase_price_per_pack = db.Column(db.Numeric(14, 2), nullable=False)
    sale_price_per_box = db.Column(db.Numeric(14, 2), nullable=False)
    sale_price_per_pack = db.Column(db.Numeric(14, 2), nullable=False)
    discount = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    line_total = db.Column(db.Numeric(14, 2), nullable=False)

    purchase = db.relationship("Purchase", back_populates="items")
    product = db.relationship("Product")


class SaleReturn(db.Model):
    __tablename__ = "sale_returns"
    id = db.Column(db.String, primary_key=True, default=gen_id)
    return_invoice_number = db.Column(db.String, unique=True, nullable=False)
    date = db.Column(db.DateTime(timezone=True), nullable=False)
    sale_id = db.Column(db.String, db.ForeignKey("sales.id"), nullable=False)
    customer_id = db.Column(db.String, db.ForeignKey("customers.id"), nullable=False)
    subtotal = db.Column(db.Numeric(14, 2), nullable=False)
    grand_total = db.Column(db.Numeric(14, 2), nullable=False)
    notes = db.Column(db.String)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    created_by_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now)

    sale = db.relationship("Sale")
    customer = db.relationship("Customer")
    items = db.relationship("SaleReturnItem", back_populates="sale_return", cascade="all, delete-orphan")


class SaleReturnItem(db.Model):
    __tablename__ = "sale_return_items"
    id = db.Column(db.String, primary_key=True, default=gen_id)
    sale_return_id = db.Column(db.String, db.ForeignKey("sale_returns.id", ondelete="CASCADE"), nullable=False)
    sale_item_id = db.Column(db.String, db.ForeignKey("sale_items.id"), nullable=False)
    product_id = db.Column(db.String, db.ForeignKey("products.id"), nullable=False)
    quantity_packs = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(14, 2), nullable=False)
    line_total = db.Column(db.Numeric(14, 2), nullable=False)

    sale_return = db.relationship("SaleReturn", back_populates="items")
    sale_item = db.relationship("SaleItem")
    product = db.relationship("Product")


class PurchaseReturn(db.Model):
    __tablename__ = "purchase_returns"
    id = db.Column(db.String, primary_key=True, default=gen_id)
    return_invoice_number = db.Column(db.String, unique=True, nullable=False)
    date = db.Column(db.DateTime(timezone=True), nullable=False)
    purchase_id = db.Column(db.String, db.ForeignKey("purchases.id"), nullable=False)
    supplier_id = db.Column(db.String, db.ForeignKey("suppliers.id"), nullable=False)
    subtotal = db.Column(db.Numeric(14, 2), nullable=False)
    grand_total = db.Column(db.Numeric(14, 2), nullable=False)
    notes = db.Column(db.String)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    created_by_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now)

    purchase = db.relationship("Purchase")
    supplier = db.relationship("Supplier")
    items = db.relationship("PurchaseReturnItem", back_populates="purchase_return", cascade="all, delete-orphan")


class PurchaseReturnItem(db.Model):
    __tablename__ = "purchase_return_items"
    id = db.Column(db.String, primary_key=True, default=gen_id)
    purchase_return_id = db.Column(db.String, db.ForeignKey("purchase_returns.id", ondelete="CASCADE"), nullable=False)
    purchase_item_id = db.Column(db.String, db.ForeignKey("purchase_items.id"), nullable=False)
    product_id = db.Column(db.String, db.ForeignKey("products.id"), nullable=False)
    quantity_packs = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(14, 2), nullable=False)
    line_total = db.Column(db.Numeric(14, 2), nullable=False)

    purchase_return = db.relationship("PurchaseReturn", back_populates="items")
    purchase_item = db.relationship("PurchaseItem")
    product = db.relationship("Product")


class StockAdjustment(db.Model):
    __tablename__ = "stock_adjustments"
    id = db.Column(db.String, primary_key=True, default=gen_id)
    product_id = db.Column(db.String, db.ForeignKey("products.id"), nullable=False)
    quantity_packs = db.Column(db.Integer, nullable=False)  # signed
    type = db.Column(db.String, nullable=False)
    reason = db.Column(db.String, nullable=False)
    date = db.Column(db.DateTime(timezone=True), nullable=False)
    user_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False)
    notes = db.Column(db.String)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now)


class OpeningStock(db.Model):
    __tablename__ = "opening_stock"
    id = db.Column(db.String, primary_key=True, default=gen_id)
    product_id = db.Column(db.String, db.ForeignKey("products.id"), nullable=False)
    quantity_packs = db.Column(db.Integer, nullable=False)
    cost_per_pack = db.Column(db.Numeric(14, 2), nullable=False)
    date = db.Column(db.DateTime(timezone=True), nullable=False)
    notes = db.Column(db.String)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now)


class OpeningDebtor(db.Model):
    __tablename__ = "opening_debtors"
    id = db.Column(db.String, primary_key=True, default=gen_id)
    customer_id = db.Column(db.String, db.ForeignKey("customers.id"), nullable=False)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    date = db.Column(db.DateTime(timezone=True), nullable=False)
    notes = db.Column(db.String)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now)


class OpeningCreditor(db.Model):
    __tablename__ = "opening_creditors"
    id = db.Column(db.String, primary_key=True, default=gen_id)
    supplier_id = db.Column(db.String, db.ForeignKey("suppliers.id"), nullable=False)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    date = db.Column(db.DateTime(timezone=True), nullable=False)
    notes = db.Column(db.String)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now)


class CustomerPayment(db.Model):
    __tablename__ = "customer_payments"
    id = db.Column(db.String, primary_key=True, default=gen_id)
    customer_id = db.Column(db.String, db.ForeignKey("customers.id"), nullable=False)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    date = db.Column(db.DateTime(timezone=True), nullable=False)
    payment_method = db.Column(db.String, nullable=False)
    notes = db.Column(db.String)
    user_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now)

    customer = db.relationship("Customer")


class SupplierPayment(db.Model):
    __tablename__ = "supplier_payments"
    id = db.Column(db.String, primary_key=True, default=gen_id)
    supplier_id = db.Column(db.String, db.ForeignKey("suppliers.id"), nullable=False)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    date = db.Column(db.DateTime(timezone=True), nullable=False)
    payment_method = db.Column(db.String, nullable=False)
    notes = db.Column(db.String)
    user_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now)

    supplier = db.relationship("Supplier")


class Expense(db.Model):
    __tablename__ = "expenses"
    id = db.Column(db.String, primary_key=True, default=gen_id)
    date = db.Column(db.DateTime(timezone=True), nullable=False)
    category = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    payment_method = db.Column(db.String, nullable=False)
    notes = db.Column(db.String)
    user_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now)


class Transaction(db.Model):
    __tablename__ = "transactions"
    id = db.Column(db.String, primary_key=True, default=gen_id)
    date = db.Column(db.DateTime(timezone=True), nullable=False)
    type = db.Column(db.String, nullable=False)  # CASH_IN | CASH_OUT
    category = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    notes = db.Column(db.String)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now)

    sale_id = db.Column(db.String, db.ForeignKey("sales.id"))
    purchase_id = db.Column(db.String, db.ForeignKey("purchases.id"))
    sale_return_id = db.Column(db.String, db.ForeignKey("sale_returns.id"))
    purchase_return_id = db.Column(db.String, db.ForeignKey("purchase_returns.id"))
    customer_payment_id = db.Column(db.String, db.ForeignKey("customer_payments.id"))
    supplier_payment_id = db.Column(db.String, db.ForeignKey("supplier_payments.id"))
    expense_id = db.Column(db.String, db.ForeignKey("expenses.id"))


class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(db.String, primary_key=True, default=gen_id)
    user_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False)
    action = db.Column(db.String, nullable=False)
    record_type = db.Column(db.String, nullable=False)
    record_id = db.Column(db.String)
    previous_value = db.Column(db.JSON)
    new_value = db.Column(db.JSON)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now)


class BusinessSettings(db.Model):
    __tablename__ = "business_settings"
    id = db.Column(db.String, primary_key=True, default="singleton")
    business_name = db.Column(db.String, nullable=False, default="My Distribution Business")
    address = db.Column(db.String)
    phone = db.Column(db.String)
    email = db.Column(db.String)
    logo_url = db.Column(db.String)
    tax_number = db.Column(db.String)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now, onupdate=now)


class InvoiceSettings(db.Model):
    __tablename__ = "invoice_settings"
    id = db.Column(db.String, primary_key=True, default="singleton")
    sale_prefix = db.Column(db.String, nullable=False, default="SALE-")
    purchase_prefix = db.Column(db.String, nullable=False, default="PURCHASE-")
    sale_return_prefix = db.Column(db.String, nullable=False, default="RETURN-SALE-")
    purchase_return_prefix = db.Column(db.String, nullable=False, default="RETURN-PURCHASE-")
    payment_receipt_prefix = db.Column(db.String, nullable=False, default="RECEIPT-")
    next_sale_number = db.Column(db.Integer, nullable=False, default=1)
    next_purchase_number = db.Column(db.Integer, nullable=False, default=1)
    next_sale_return_number = db.Column(db.Integer, nullable=False, default=1)
    next_purchase_return_number = db.Column(db.Integer, nullable=False, default=1)
    next_receipt_number = db.Column(db.Integer, nullable=False, default=1)
    number_padding = db.Column(db.Integer, nullable=False, default=6)
    invoice_footer = db.Column(db.String)
    default_notes = db.Column(db.String)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now, onupdate=now)


class PrintingSettings(db.Model):
    __tablename__ = "printing_settings"
    id = db.Column(db.String, primary_key=True, default="singleton")
    paper_size = db.Column(db.String, nullable=False, default="A4")
    show_logo = db.Column(db.Boolean, nullable=False, default=True)
    show_business_info = db.Column(db.Boolean, nullable=False, default=True)
    show_customer_info = db.Column(db.Boolean, nullable=False, default=True)
    margin_mm = db.Column(db.Integer, nullable=False, default=10)
    footer_text = db.Column(db.String)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now, onupdate=now)


class Backup(db.Model):
    __tablename__ = "backups"
    id = db.Column(db.String, primary_key=True, default=gen_id)
    filename = db.Column(db.String, nullable=False)
    size_bytes = db.Column(db.Integer, nullable=False)
    created_by_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now)
