"""
Per-user, per-module permissions.

ADMIN role always has full access and bypasses the permissions list
entirely — this is deliberate: permissions are something an admin grants,
so an admin can never accidentally lock themselves out by unchecking their
own boxes, and there is never a scenario where zero people can manage the
system.

For every other role, access to a module is granted only if its key is
present in `user.permissions` (a JSON list of strings stored on the User
row), set by an admin on the Users screen.
"""

from functools import wraps

from flask import abort
from flask_login import current_user

# (key, label, group) — group matches the sidebar section names so the
# permissions checklist on the Add/Edit User form can be rendered in the
# same shape as the sidebar itself.
PERMISSION_MODULES = [
    ("sales", "Sales", "Sales"),
    ("sale_returns", "Sale Returns", "Sales"),
    ("customers", "Customers", "Sales"),
    ("debtors", "Debtors", "Sales"),
    ("purchases", "Purchases", "Purchases"),
    ("purchase_returns", "Purchase Returns", "Purchases"),
    ("suppliers", "Suppliers", "Purchases"),
    ("creditors", "Creditors", "Purchases"),
    ("products", "Products", "Inventory"),
    ("stock", "Stock", "Inventory"),
    ("stock_adjustments", "Stock Adjustments", "Inventory"),
    ("stock_opening", "Opening Balances", "Inventory"),
    ("transactions", "Cash Book", "Money"),
    ("expenses", "Expenses", "Money"),
    ("employees", "Employees", "Business"),
    ("invoices", "Invoices", "Business"),
    ("reports", "Reports", "Business"),
    ("load_card", "Load Card", "Business"),
    ("backup", "Backup & Restore", "System"),
    ("settings", "Settings", "System"),
]

PERMISSION_KEYS = [key for key, _, _ in PERMISSION_MODULES]

# Blueprint name -> required permission key. Blueprints not listed here
# (main, auth, account) have no module gate — main.dashboard is always
# reachable once logged in, and auth/account handle their own access.
BLUEPRINT_PERMISSION_MAP = {
    "sales": "sales",
    "sale_returns": "sale_returns",
    "customers": "customers",
    "debtors": "debtors",
    "purchases": "purchases",
    "purchase_returns": "purchase_returns",
    "suppliers": "suppliers",
    "creditors": "creditors",
    "products": "products",
    "stock_module": "stock",
    "stock_adjustments": "stock_adjustments",
    "opening_balances": "stock_opening",
    "transactions": "transactions",
    "expenses": "expenses",
    "employees": "employees",
    "invoices": "invoices",
    "reports": "reports",
    "load_card": "load_card",
    "backup": "backup",
    "settings": "settings",
}


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "ADMIN":
            abort(403)
        return view(*args, **kwargs)

    return wrapped
