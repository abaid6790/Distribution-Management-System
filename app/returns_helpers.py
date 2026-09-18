from sqlalchemy import func

from app.extensions import db
from app.models import SaleReturnItem, SaleReturn, PurchaseReturnItem, PurchaseReturn


def get_already_returned_for_sale_items(sale_item_ids):
    if not sale_item_ids:
        return {}
    rows = (
        db.session.query(SaleReturnItem.sale_item_id, func.coalesce(func.sum(SaleReturnItem.quantity_packs), 0))
        .join(SaleReturn, SaleReturnItem.sale_return_id == SaleReturn.id)
        .filter(SaleReturn.is_deleted.is_(False), SaleReturnItem.sale_item_id.in_(sale_item_ids))
        .group_by(SaleReturnItem.sale_item_id)
        .all()
    )
    return {row[0]: int(row[1]) for row in rows}


def get_already_returned_for_purchase_items(purchase_item_ids):
    if not purchase_item_ids:
        return {}
    rows = (
        db.session.query(
            PurchaseReturnItem.purchase_item_id, func.coalesce(func.sum(PurchaseReturnItem.quantity_packs), 0)
        )
        .join(PurchaseReturn, PurchaseReturnItem.purchase_return_id == PurchaseReturn.id)
        .filter(PurchaseReturn.is_deleted.is_(False), PurchaseReturnItem.purchase_item_id.in_(purchase_item_ids))
        .group_by(PurchaseReturnItem.purchase_item_id)
        .all()
    )
    return {row[0]: int(row[1]) for row in rows}
