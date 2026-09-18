from datetime import datetime, date

from flask import Flask, redirect, url_for, request, render_template
from flask_login import current_user

from app.extensions import db, migrate, login_manager
from app.permissions import PERMISSION_MODULES, BLUEPRINT_PERMISSION_MAP
from config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, user_id)

    # ── Template helpers ────────────────────────────────────────────
    @app.template_filter("money")
    def money_filter(value):
        try:
            n = float(value)
        except (TypeError, ValueError):
            n = 0
        return "Rs {:,.0f}".format(n)

    @app.template_filter("money2")
    def money2_filter(value):
        try:
            n = float(value)
        except (TypeError, ValueError):
            n = 0
        return "Rs {:,.2f}".format(n)

    @app.template_filter("shortdate")
    def shortdate_filter(value):
        if value is None:
            return "—"
        if isinstance(value, (datetime, date)):
            return value.strftime("%d %b %Y")
        return str(value)

    # ── Access control ──────────────────────────────────────────────
    # Endpoints reachable regardless of permissions/forced-password-change,
    # so a locked-out state is never possible.
    ALWAYS_ALLOWED_ENDPOINTS = {
        "auth.login",
        "auth.logout",
        "account.change_password",
        "static",
    }

    @app.before_request
    def enforce_access():
        if not current_user.is_authenticated:
            return None
        if request.endpoint in ALWAYS_ALLOWED_ENDPOINTS or request.endpoint is None:
            return None

        if current_user.must_change_password:
            return redirect(url_for("account.change_password"))

        blueprint = request.blueprint
        required = BLUEPRINT_PERMISSION_MAP.get(blueprint)
        if required and not current_user.has_permission(required):
            return render_template("403.html"), 403

        return None

    @app.context_processor
    def inject_globals():
        nav_groups = []
        if current_user.is_authenticated:
            allowed = lambda key: current_user.has_permission(key)  # noqa: E731
            all_groups = [
                {
                    "title": "Overview",
                    "links": [{"href": "/dashboard", "label": "Dashboard", "perm": None}],
                },
                {
                    "title": "Sales",
                    "links": [
                        {"href": "/sales", "label": "Sales", "perm": "sales"},
                        {"href": "/sale-returns", "label": "Sale Returns", "perm": "sale_returns"},
                        {"href": "/customers", "label": "Customers", "perm": "customers"},
                        {"href": "/debtors", "label": "Debtors", "perm": "debtors"},
                    ],
                },
                {
                    "title": "Purchases",
                    "links": [
                        {"href": "/purchases", "label": "Purchases", "perm": "purchases"},
                        {"href": "/purchase-returns", "label": "Purchase Returns", "perm": "purchase_returns"},
                        {"href": "/suppliers", "label": "Suppliers", "perm": "suppliers"},
                        {"href": "/creditors", "label": "Creditors", "perm": "creditors"},
                    ],
                },
                {
                    "title": "Inventory",
                    "links": [
                        {"href": "/products", "label": "Products", "perm": "products"},
                        {"href": "/stock", "label": "Stock", "perm": "stock"},
                        {"href": "/stock/adjustments", "label": "Stock Adjustments", "perm": "stock_adjustments"},
                        {"href": "/stock/low", "label": "Low Stock", "perm": "stock"},
                        {"href": "/stock/opening", "label": "Opening Balances", "perm": "stock_opening"},
                    ],
                },
                {
                    "title": "Money",
                    "links": [
                        {"href": "/transactions", "label": "Cash Book", "perm": "transactions"},
                        {"href": "/expenses", "label": "Expenses", "perm": "expenses"},
                    ],
                },
                {
                    "title": "Business",
                    "links": [
                        {"href": "/employees", "label": "Employees", "perm": "employees"},
                        {"href": "/invoices", "label": "Invoices", "perm": "invoices"},
                        {"href": "/reports", "label": "Reports", "perm": "reports"},
                        {"href": "/load-card", "label": "Load Card", "perm": "load_card"},
                    ],
                },
                {
                    "title": "System",
                    "links": [
                        {"href": "/backup", "label": "Backup & Restore", "perm": "backup"},
                        {"href": "/settings", "label": "Settings", "perm": "settings"},
                        {"href": "/users", "label": "Users", "perm": "__admin_only__"},
                    ],
                },
            ]

            for group in all_groups:
                visible_links = [
                    link
                    for link in group["links"]
                    if link["perm"] is None
                    or (link["perm"] == "__admin_only__" and current_user.role == "ADMIN")
                    or (link["perm"] not in (None, "__admin_only__") and allowed(link["perm"]))
                ]
                if visible_links:
                    nav_groups.append({"title": group["title"], "links": visible_links})

        return {"today_str": datetime.now().strftime("%A, %d %B %Y"), "nav_groups": nav_groups}

    # ── Blueprints ───────────────────────────────────────────────────
    from app.auth.routes import auth_bp
    from app.account.routes import account_bp
    from app.main.routes import main_bp
    from app.products.routes import products_bp
    from app.employees.routes import employees_bp
    from app.settings.routes import settings_bp
    from app.purchases.routes import purchases_bp
    from app.sales.routes import sales_bp
    from app.customers.routes import customers_bp
    from app.suppliers.routes import suppliers_bp
    from app.sale_returns.routes import sale_returns_bp
    from app.purchase_returns.routes import purchase_returns_bp
    from app.debtors.routes import debtors_bp
    from app.creditors.routes import creditors_bp
    from app.expenses.routes import expenses_bp
    from app.transactions.routes import transactions_bp
    from app.stock_module.routes import stock_bp
    from app.reports.routes import reports_bp
    from app.load_card.routes import load_card_bp
    from app.stock_adjustments.routes import stock_adjustments_bp
    from app.opening_balances.routes import opening_bp
    from app.invoices.routes import invoices_bp
    from app.backup.routes import backup_bp
    from app.users.routes import users_bp
    from app.stubs.routes import stubs_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(purchases_bp)
    app.register_blueprint(sales_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(suppliers_bp)
    app.register_blueprint(sale_returns_bp)
    app.register_blueprint(purchase_returns_bp)
    app.register_blueprint(debtors_bp)
    app.register_blueprint(creditors_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(stock_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(load_card_bp)
    app.register_blueprint(stock_adjustments_bp)
    app.register_blueprint(opening_bp)
    app.register_blueprint(invoices_bp)
    app.register_blueprint(backup_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(stubs_bp)

    return app
