"""
Debtor balance (per customer) =
    Credit portion of their non-deleted sales
  - Grand total of non-deleted sale returns against those sales
  - Payments received from that customer

Creditor balance (per supplier) is the mirror image using purchases.

This is the ONLY place these balances are calculated — Debtors/Creditors
pages, the Customers/Suppliers lists, and the Dashboard all read from here
so the numbers never drift apart.
"""

from sqlalchemy import func

from app.extensions import db
from app.models import Sale, SaleReturn, CustomerPayment, Purchase, PurchaseReturn, SupplierPayment, OpeningDebtor, OpeningCreditor


def get_debtor_balances(customer_ids=None):
    credit_q = db.session.query(Sale.customer_id, func.coalesce(func.sum(Sale.credit_amount), 0)).filter(
        Sale.is_deleted.is_(False)
    )
    returns_q = (
        db.session.query(SaleReturn.customer_id, func.coalesce(func.sum(SaleReturn.grand_total), 0))
        .filter(SaleReturn.is_deleted.is_(False))
    )
    payments_q = db.session.query(CustomerPayment.customer_id, func.coalesce(func.sum(CustomerPayment.amount), 0))
    opening_q = db.session.query(OpeningDebtor.customer_id, func.coalesce(func.sum(OpeningDebtor.amount), 0))

    if customer_ids:
        credit_q = credit_q.filter(Sale.customer_id.in_(customer_ids))
        returns_q = returns_q.filter(SaleReturn.customer_id.in_(customer_ids))
        payments_q = payments_q.filter(CustomerPayment.customer_id.in_(customer_ids))
        opening_q = opening_q.filter(OpeningDebtor.customer_id.in_(customer_ids))

    credit_map = dict(credit_q.group_by(Sale.customer_id).all())
    returns_map = dict(returns_q.group_by(SaleReturn.customer_id).all())
    payments_map = dict(payments_q.group_by(CustomerPayment.customer_id).all())
    opening_map = dict(opening_q.group_by(OpeningDebtor.customer_id).all())

    ids = customer_ids or set(credit_map) | set(returns_map) | set(payments_map) | set(opening_map)
    result = {}
    for cid in ids:
        credit = float(credit_map.get(cid, 0)) + float(opening_map.get(cid, 0))
        returns = float(returns_map.get(cid, 0))
        paid = float(payments_map.get(cid, 0))
        result[cid] = {
            "total_credit": credit,
            "total_returns": returns,
            "total_paid": paid,
            "pending": max(0.0, credit - returns - paid),
        }
    return result


def get_debtor_balance(customer_id):
    return get_debtor_balances([customer_id]).get(
        customer_id, {"total_credit": 0, "total_returns": 0, "total_paid": 0, "pending": 0}
    )


def get_creditor_balances(supplier_ids=None):
    credit_q = db.session.query(Purchase.supplier_id, func.coalesce(func.sum(Purchase.credit_amount), 0)).filter(
        Purchase.is_deleted.is_(False)
    )
    returns_q = (
        db.session.query(PurchaseReturn.supplier_id, func.coalesce(func.sum(PurchaseReturn.grand_total), 0))
        .filter(PurchaseReturn.is_deleted.is_(False))
    )
    payments_q = db.session.query(SupplierPayment.supplier_id, func.coalesce(func.sum(SupplierPayment.amount), 0))
    opening_q = db.session.query(OpeningCreditor.supplier_id, func.coalesce(func.sum(OpeningCreditor.amount), 0))

    if supplier_ids:
        credit_q = credit_q.filter(Purchase.supplier_id.in_(supplier_ids))
        returns_q = returns_q.filter(PurchaseReturn.supplier_id.in_(supplier_ids))
        payments_q = payments_q.filter(SupplierPayment.supplier_id.in_(supplier_ids))
        opening_q = opening_q.filter(OpeningCreditor.supplier_id.in_(supplier_ids))

    credit_map = dict(credit_q.group_by(Purchase.supplier_id).all())
    returns_map = dict(returns_q.group_by(PurchaseReturn.supplier_id).all())
    payments_map = dict(payments_q.group_by(SupplierPayment.supplier_id).all())
    opening_map = dict(opening_q.group_by(OpeningCreditor.supplier_id).all())

    ids = supplier_ids or set(credit_map) | set(returns_map) | set(payments_map) | set(opening_map)
    result = {}
    for sid in ids:
        credit = float(credit_map.get(sid, 0)) + float(opening_map.get(sid, 0))
        returns = float(returns_map.get(sid, 0))
        paid = float(payments_map.get(sid, 0))
        result[sid] = {
            "total_credit": credit,
            "total_returns": returns,
            "total_paid": paid,
            "pending": max(0.0, credit - returns - paid),
        }
    return result


def get_creditor_balance(supplier_id):
    return get_creditor_balances([supplier_id]).get(
        supplier_id, {"total_credit": 0, "total_returns": 0, "total_paid": 0, "pending": 0}
    )
