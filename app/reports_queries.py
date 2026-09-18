from sqlalchemy import func

from app.extensions import db
from app.models import (
    Sale,
    SaleItem,
    Purchase,
    PurchaseItem,
    Customer,
    Supplier,
    Employee,
    Expense,
    SaleReturn,
    SaleReturnItem,
    PurchaseReturn,
    PurchaseReturnItem,
)
from app.stock import get_average_cost_per_pack
from app.balances import get_debtor_balances, get_creditor_balances


def get_sales_report(start, end):
    rows = (
        db.session.query(Sale, Customer, Employee)
        .join(Customer, Sale.customer_id == Customer.id)
        .join(Employee, Sale.booked_by_id == Employee.id)
        .filter(Sale.is_deleted.is_(False), Sale.date >= start, Sale.date < end)
        .order_by(Sale.date.desc())
        .all()
    )
    item_counts = dict(
        db.session.query(SaleItem.sale_id, func.count(SaleItem.id)).group_by(SaleItem.sale_id).all()
    )
    return [
        {"sale": s, "customer": c, "employee": e, "item_count": item_counts.get(s.id, 0)} for s, c, e in rows
    ]


def get_purchase_report(start, end):
    rows = (
        db.session.query(Purchase, Supplier)
        .join(Supplier, Purchase.supplier_id == Supplier.id)
        .filter(Purchase.is_deleted.is_(False), Purchase.date >= start, Purchase.date < end)
        .order_by(Purchase.date.desc())
        .all()
    )
    item_counts = dict(
        db.session.query(PurchaseItem.purchase_id, func.count(PurchaseItem.id)).group_by(PurchaseItem.purchase_id).all()
    )
    return [{"purchase": p, "supplier": s, "item_count": item_counts.get(p.id, 0)} for p, s in rows]


def get_expense_report(start, end):
    return Expense.query.filter(Expense.date >= start, Expense.date < end).order_by(Expense.date.desc()).all()


def get_sale_return_report(start, end):
    rows = (
        db.session.query(SaleReturn, Sale, Customer)
        .join(Sale, SaleReturn.sale_id == Sale.id)
        .join(Customer, SaleReturn.customer_id == Customer.id)
        .filter(SaleReturn.is_deleted.is_(False), SaleReturn.date >= start, SaleReturn.date < end)
        .order_by(SaleReturn.date.desc())
        .all()
    )
    qty_by_return = dict(
        db.session.query(SaleReturnItem.sale_return_id, func.coalesce(func.sum(SaleReturnItem.quantity_packs), 0))
        .group_by(SaleReturnItem.sale_return_id)
        .all()
    )
    return [
        {"return": r, "sale": s, "customer": c, "quantity": qty_by_return.get(r.id, 0)} for r, s, c in rows
    ]


def get_purchase_return_report(start, end):
    rows = (
        db.session.query(PurchaseReturn, Purchase, Supplier)
        .join(Purchase, PurchaseReturn.purchase_id == Purchase.id)
        .join(Supplier, PurchaseReturn.supplier_id == Supplier.id)
        .filter(PurchaseReturn.is_deleted.is_(False), PurchaseReturn.date >= start, PurchaseReturn.date < end)
        .order_by(PurchaseReturn.date.desc())
        .all()
    )
    qty_by_return = dict(
        db.session.query(PurchaseReturnItem.purchase_return_id, func.coalesce(func.sum(PurchaseReturnItem.quantity_packs), 0))
        .group_by(PurchaseReturnItem.purchase_return_id)
        .all()
    )
    return [
        {"return": r, "purchase": p, "supplier": s, "quantity": qty_by_return.get(r.id, 0)} for r, p, s in rows
    ]


def get_debtor_report():
    customers = Customer.query.order_by(Customer.name).all()
    balances = get_debtor_balances([c.id for c in customers])
    rows = [{"customer": c, "balance": balances.get(c.id, {"total_credit": 0, "total_paid": 0, "pending": 0})} for c in customers]
    return [r for r in rows if r["balance"]["total_credit"] > 0]


def get_creditor_report():
    suppliers = Supplier.query.order_by(Supplier.name).all()
    balances = get_creditor_balances([s.id for s in suppliers])
    rows = [{"supplier": s, "balance": balances.get(s.id, {"total_credit": 0, "total_paid": 0, "pending": 0})} for s in suppliers]
    return [r for r in rows if r["balance"]["total_credit"] > 0]


def get_profit_and_loss(start, end):
    sales_total = float(
        db.session.query(func.coalesce(func.sum(Sale.grand_total), 0))
        .filter(Sale.is_deleted.is_(False), Sale.date >= start, Sale.date < end)
        .scalar()
        or 0
    )
    sale_returns_total = float(
        db.session.query(func.coalesce(func.sum(SaleReturn.grand_total), 0))
        .filter(SaleReturn.is_deleted.is_(False), SaleReturn.date >= start, SaleReturn.date < end)
        .scalar()
        or 0
    )
    net_sales = sales_total - sale_returns_total

    # COGS: quantity sold (net of returns) in the period, valued at each
    # product's weighted-average purchase cost per pack (see app/stock.py).
    sold_by_product = dict(
        db.session.query(SaleItem.product_id, func.coalesce(func.sum(SaleItem.quantity_packs), 0))
        .join(Sale, SaleItem.sale_id == Sale.id)
        .filter(Sale.is_deleted.is_(False), Sale.date >= start, Sale.date < end)
        .group_by(SaleItem.product_id)
        .all()
    )
    returned_by_product = dict(
        db.session.query(SaleReturnItem.product_id, func.coalesce(func.sum(SaleReturnItem.quantity_packs), 0))
        .join(SaleReturn, SaleReturnItem.sale_return_id == SaleReturn.id)
        .filter(SaleReturn.is_deleted.is_(False), SaleReturn.date >= start, SaleReturn.date < end)
        .group_by(SaleReturnItem.product_id)
        .all()
    )
    product_ids = set(sold_by_product) | set(returned_by_product)
    avg_cost = get_average_cost_per_pack(list(product_ids)) if product_ids else {}

    cogs = 0.0
    for pid in product_ids:
        net_packs = float(sold_by_product.get(pid, 0)) - float(returned_by_product.get(pid, 0))
        cogs += net_packs * avg_cost.get(pid, 0)

    gross_profit = net_sales - cogs

    expenses_total = float(
        db.session.query(func.coalesce(func.sum(Expense.amount), 0))
        .filter(Expense.date >= start, Expense.date < end)
        .scalar()
        or 0
    )

    net_profit = gross_profit - expenses_total

    return {
        "sales": sales_total,
        "sale_returns": sale_returns_total,
        "net_sales": net_sales,
        "cogs": cogs,
        "gross_profit": gross_profit,
        "expenses": expenses_total,
        "net_profit": net_profit,
    }
