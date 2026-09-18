from datetime import datetime, timedelta

from sqlalchemy import func, and_

from app.extensions import db
from app.models import (
    Sale,
    Purchase,
    SaleReturn,
    PurchaseReturn,
    Expense,
    Transaction,
    Product,
    Customer,
    Supplier,
    Employee,
)
from app.stock import get_stock_map
from app.balances import get_debtor_balances, get_creditor_balances


def _today_range():
    start = datetime.combine(datetime.now().date(), datetime.min.time())
    end = start + timedelta(days=1)
    return start, end


def _sum_between(model, amount_col, guard_deleted=True):
    start, end = _today_range()
    q = db.session.query(func.coalesce(func.sum(amount_col), 0)).filter(model.date >= start, model.date < end)
    if guard_deleted and hasattr(model, "is_deleted"):
        q = q.filter(model.is_deleted.is_(False))
    return float(q.scalar() or 0)


def get_dashboard_summary():
    start, end = _today_range()

    today_sales = _sum_between(Sale, Sale.grand_total)
    today_purchases = _sum_between(Purchase, Purchase.grand_total)
    today_sale_returns = _sum_between(SaleReturn, SaleReturn.grand_total, guard_deleted=True)
    today_purchase_returns = _sum_between(PurchaseReturn, PurchaseReturn.grand_total, guard_deleted=True)
    today_expenses = _sum_between(Expense, Expense.amount, guard_deleted=False)

    today_cash_in = float(
        db.session.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(Transaction.type == "CASH_IN", Transaction.date >= start, Transaction.date < end)
        .scalar()
        or 0
    )
    today_cash_out = float(
        db.session.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(Transaction.type == "CASH_OUT", Transaction.date >= start, Transaction.date < end)
        .scalar()
        or 0
    )

    products = Product.query.all()
    stock_map = get_stock_map([p.id for p in products])

    total_stock_value = 0.0
    potential_sales_value = 0.0
    low_stock_count = 0
    out_of_stock_count = 0

    for p in products:
        current = stock_map.get(p.id, 0)
        if current <= 0:
            out_of_stock_count += 1
        elif current < p.min_stock_level_packs:
            low_stock_count += 1
        total_stock_value += current * float(p.purchase_price_per_pack)
        potential_sales_value += current * float(p.sale_price_per_pack)

    total_debtors = sum(b["pending"] for b in get_debtor_balances().values())
    total_creditors = sum(b["pending"] for b in get_creditor_balances().values())

    return {
        "today_sales": today_sales,
        "today_purchases": today_purchases,
        "today_sale_returns": today_sale_returns,
        "today_purchase_returns": today_purchase_returns,
        "today_expenses": today_expenses,
        "today_cash_in": today_cash_in,
        "today_cash_out": today_cash_out,
        "today_profit": today_sales - today_sale_returns - today_expenses,
        "total_debtors": max(0.0, total_debtors),
        "total_creditors": max(0.0, total_creditors),
        "total_stock_value": total_stock_value,
        "potential_sales_value": potential_sales_value,
        "low_stock_count": low_stock_count,
        "out_of_stock_count": out_of_stock_count,
    }


def get_recent_sales(limit=6):
    return (
        db.session.query(Sale, Customer, Employee)
        .join(Customer, Sale.customer_id == Customer.id)
        .join(Employee, Sale.booked_by_id == Employee.id)
        .filter(Sale.is_deleted.is_(False))
        .order_by(Sale.created_at.desc())
        .limit(limit)
        .all()
    )


def get_recent_purchases(limit=6):
    return (
        db.session.query(Purchase, Supplier)
        .join(Supplier, Purchase.supplier_id == Supplier.id)
        .filter(Purchase.is_deleted.is_(False))
        .order_by(Purchase.created_at.desc())
        .limit(limit)
        .all()
    )


def get_low_stock_products(limit=8):
    products = Product.query.filter_by(is_active=True).all()
    stock_map = get_stock_map([p.id for p in products])

    rows = []
    for p in products:
        current = stock_map.get(p.id, 0)
        if current <= 0:
            status = "out"
        elif current < p.min_stock_level_packs:
            status = "low"
        else:
            status = "normal"
        if status != "normal":
            rows.append({"id": p.id, "name": p.name, "current_stock": current, "min_stock": p.min_stock_level_packs, "status": status})

    return rows[:limit]


def get_recent_transactions(limit=8):
    return Transaction.query.order_by(Transaction.created_at.desc()).limit(limit).all()


def get_counts():
    return {
        "products": Product.query.count(),
        "customers": Customer.query.count(),
        "suppliers": Supplier.query.count(),
        "employees": Employee.query.count(),
    }
