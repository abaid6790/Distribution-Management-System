from datetime import datetime, timedelta
import calendar


def resolve_range(range_key: str, from_str: str = "", to_str: str = ""):
    """Returns (start, end_exclusive, label) as datetimes for the given range key."""
    today = datetime.now().date()

    if range_key == "yesterday":
        d = today - timedelta(days=1)
        start = datetime.combine(d, datetime.min.time())
        end = start + timedelta(days=1)
        return start, end, "Yesterday"

    if range_key == "month":
        start = datetime(today.year, today.month, 1)
        last_day = calendar.monthrange(today.year, today.month)[1]
        end = datetime(today.year, today.month, last_day) + timedelta(days=1)
        return start, end, "This Month"

    if range_key == "year":
        start = datetime(today.year, 1, 1)
        end = datetime(today.year + 1, 1, 1)
        return start, end, "This Year"

    if range_key == "custom" and from_str and to_str:
        start = datetime.strptime(from_str, "%Y-%m-%d")
        end = datetime.strptime(to_str, "%Y-%m-%d") + timedelta(days=1)
        return start, end, f"{from_str} to {to_str}"

    # default: today
    start = datetime.combine(today, datetime.min.time())
    end = start + timedelta(days=1)
    return start, end, "Today"
