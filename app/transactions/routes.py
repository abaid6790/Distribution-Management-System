from datetime import datetime, timedelta

from flask import Blueprint, render_template, request
from flask_login import login_required

from app.models import Transaction

transactions_bp = Blueprint("transactions", __name__, url_prefix="/transactions")


@transactions_bp.route("/")
@login_required
def list_transactions():
    from_str = request.args.get("from", "")
    to_str = request.args.get("to", "")
    type_filter = request.args.get("type", "")

    query = Transaction.query
    if from_str:
        query = query.filter(Transaction.date >= datetime.strptime(from_str, "%Y-%m-%d"))
    if to_str:
        to_date = datetime.strptime(to_str, "%Y-%m-%d") + timedelta(days=1)
        query = query.filter(Transaction.date < to_date)
    if type_filter in ("CASH_IN", "CASH_OUT"):
        query = query.filter(Transaction.type == type_filter)

    # Running balance is computed over ALL transactions up to the filtered
    # window's start so the balance column always reflects reality, not
    # just the filtered subset.
    all_before = Transaction.query
    if from_str:
        all_before = all_before.filter(Transaction.date < datetime.strptime(from_str, "%Y-%m-%d"))
    else:
        all_before = all_before.filter(Transaction.date < datetime.min)

    opening_balance = 0.0
    if from_str:
        earlier = Transaction.query.filter(Transaction.date < datetime.strptime(from_str, "%Y-%m-%d")).order_by(
            Transaction.date.asc(), Transaction.created_at.asc()
        ).all()
        for t in earlier:
            opening_balance += float(t.amount) if t.type == "CASH_IN" else -float(t.amount)

    rows_asc = query.order_by(Transaction.date.asc(), Transaction.created_at.asc()).all()

    running = opening_balance
    display_rows = []
    for t in rows_asc:
        running += float(t.amount) if t.type == "CASH_IN" else -float(t.amount)
        display_rows.append({"tx": t, "balance": running})

    display_rows.reverse()
    closing_balance = running

    return render_template(
        "transactions/list.html",
        rows=display_rows,
        opening_balance=opening_balance,
        closing_balance=closing_balance,
        from_str=from_str,
        to_str=to_str,
        type_filter=type_filter,
    )
