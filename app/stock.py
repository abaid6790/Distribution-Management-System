"""
Current Stock (packs) =
    Opening Stock
  + Purchases
  + Sale Returns
  - Sales
  - Purchase Returns
  +/- Stock Adjustments

This is the ONLY place stock is calculated. Dashboard, Stock module,
Low Stock, Reports, and Sales validation all call through here so numbers
never drift between modules.
"""

from sqlalchemy import func

from app.extensions import db
from app.models import (
    OpeningStock,
    PurchaseItem,
    Purchase,
    SaleItem,
    Sale,
    SaleReturnItem,
    SaleReturn,
    PurchaseReturnItem,
    PurchaseReturn,
    StockAdjustment,
)


def get_stock_map(product_ids=None):
    """Returns {product_id: current_stock_packs} for the given products (or all)."""

    def agg(model, qty_col, product_col, join_model=None, join_cond=None, guard=None):
        q = db.session.query(product_col, func.coalesce(func.sum(qty_col), 0))
        if join_model is not None:
            q = q.join(join_model, join_cond)
        if guard is not None:
            q = q.filter(guard)
        if product_ids:
            q = q.filter(product_col.in_(product_ids))
        return {row[0]: float(row[1]) for row in q.group_by(product_col).all()}

    opening = agg(OpeningStock, OpeningStock.quantity_packs, OpeningStock.product_id)
    purchased = agg(
        PurchaseItem,
        PurchaseItem.quantity_packs,
        PurchaseItem.product_id,
        Purchase,
        PurchaseItem.purchase_id == Purchase.id,
        Purchase.is_deleted.is_(False),
    )
    sold = agg(
        SaleItem,
        SaleItem.quantity_packs,
        SaleItem.product_id,
        Sale,
        SaleItem.sale_id == Sale.id,
        Sale.is_deleted.is_(False),
    )
    sale_returned = agg(
        SaleReturnItem,
        SaleReturnItem.quantity_packs,
        SaleReturnItem.product_id,
        SaleReturn,
        SaleReturnItem.sale_return_id == SaleReturn.id,
        SaleReturn.is_deleted.is_(False),
    )
    purchase_returned = agg(
        PurchaseReturnItem,
        PurchaseReturnItem.quantity_packs,
        PurchaseReturnItem.product_id,
        PurchaseReturn,
        PurchaseReturnItem.purchase_return_id == PurchaseReturn.id,
        PurchaseReturn.is_deleted.is_(False),
    )
    adjusted = agg(StockAdjustment, StockAdjustment.quantity_packs, StockAdjustment.product_id)

    result = {}
    for pid, qty in opening.items():
        result[pid] = result.get(pid, 0) + qty
    for pid, qty in purchased.items():
        result[pid] = result.get(pid, 0) + qty
    for pid, qty in sale_returned.items():
        result[pid] = result.get(pid, 0) + qty
    for pid, qty in sold.items():
        result[pid] = result.get(pid, 0) - qty
    for pid, qty in purchase_returned.items():
        result[pid] = result.get(pid, 0) - qty
    for pid, qty in adjusted.items():
        result[pid] = result.get(pid, 0) + qty  # already signed

    return result


def get_stock_for_product(product_id):
    return get_stock_map([product_id]).get(product_id, 0)


def get_stock_detail_map(product_ids=None):
    """
    Returns {product_id: {purchased, sold, sale_returned, purchase_returned,
    opening, adjusted, remaining}} — the full breakdown behind the net
    current-stock figure, used by the Stock module report.
    """

    def agg(model, qty_col, product_col, join_model=None, join_cond=None, guard=None):
        q = db.session.query(product_col, func.coalesce(func.sum(qty_col), 0))
        if join_model is not None:
            q = q.join(join_model, join_cond)
        if guard is not None:
            q = q.filter(guard)
        if product_ids:
            q = q.filter(product_col.in_(product_ids))
        return {row[0]: float(row[1]) for row in q.group_by(product_col).all()}

    opening = agg(OpeningStock, OpeningStock.quantity_packs, OpeningStock.product_id)
    purchased = agg(
        PurchaseItem,
        PurchaseItem.quantity_packs,
        PurchaseItem.product_id,
        Purchase,
        PurchaseItem.purchase_id == Purchase.id,
        Purchase.is_deleted.is_(False),
    )
    sold = agg(
        SaleItem,
        SaleItem.quantity_packs,
        SaleItem.product_id,
        Sale,
        SaleItem.sale_id == Sale.id,
        Sale.is_deleted.is_(False),
    )
    sale_returned = agg(
        SaleReturnItem,
        SaleReturnItem.quantity_packs,
        SaleReturnItem.product_id,
        SaleReturn,
        SaleReturnItem.sale_return_id == SaleReturn.id,
        SaleReturn.is_deleted.is_(False),
    )
    purchase_returned = agg(
        PurchaseReturnItem,
        PurchaseReturnItem.quantity_packs,
        PurchaseReturnItem.product_id,
        PurchaseReturn,
        PurchaseReturnItem.purchase_return_id == PurchaseReturn.id,
        PurchaseReturn.is_deleted.is_(False),
    )
    adjusted = agg(StockAdjustment, StockAdjustment.quantity_packs, StockAdjustment.product_id)

    ids = product_ids or set(opening) | set(purchased) | set(sold) | set(sale_returned) | set(purchase_returned) | set(adjusted)

    result = {}
    for pid in ids:
        o = opening.get(pid, 0)
        p = purchased.get(pid, 0)
        s = sold.get(pid, 0)
        sr = sale_returned.get(pid, 0)
        pr = purchase_returned.get(pid, 0)
        adj = adjusted.get(pid, 0)
        result[pid] = {
            "opening": o,
            "purchased": p,
            "sold": s,
            "sale_returned": sr,
            "purchase_returned": pr,
            "adjusted": adj,
            "remaining": o + p + sr - s - pr + adj,
        }
    return result


def get_average_cost_per_pack(product_ids=None):
    """
    Weighted-average purchase cost per pack, computed from actual purchase
    history (not the product's current listed price) — used for
    Cost-of-Goods-Sold in Profit & Loss, per the spec's costing requirement.
    """
    q = (
        db.session.query(
            PurchaseItem.product_id,
            func.sum(PurchaseItem.quantity_packs).label("packs"),
            func.sum(PurchaseItem.quantity_packs * PurchaseItem.purchase_price_per_pack).label("cost"),
        )
        .join(Purchase, PurchaseItem.purchase_id == Purchase.id)
        .filter(Purchase.is_deleted.is_(False))
    )
    if product_ids:
        q = q.filter(PurchaseItem.product_id.in_(product_ids))
    rows = q.group_by(PurchaseItem.product_id).all()

    return {row[0]: (float(row.cost) / float(row.packs) if row.packs else 0.0) for row in rows}
