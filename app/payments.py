from dataclasses import dataclass
from typing import Optional


@dataclass
class PaymentResolution:
    cash_amount: float
    credit_amount: float
    payment_status: str
    error: Optional[str] = None


def round2(n: float) -> float:
    return round(n * 100) / 100


def resolve_payment(grand_total: float, payment_method: str, requested_cash_amount: float) -> PaymentResolution:
    if payment_method == "CASH":
        return PaymentResolution(round2(grand_total), 0.0, "PAID")

    if payment_method == "CREDIT":
        return PaymentResolution(0.0, round2(grand_total), "CREDIT")

    # PARTIAL
    if requested_cash_amount > grand_total + 0.01:
        return PaymentResolution(0.0, 0.0, "CREDIT", error="Payment can't exceed the grand total.")

    cash_amount = round2(requested_cash_amount)
    credit_amount = round2(grand_total - cash_amount)
    if credit_amount <= 0.01:
        status = "PAID"
    elif cash_amount <= 0.01:
        status = "CREDIT"
    else:
        status = "PARTIALLY_PAID"

    return PaymentResolution(cash_amount, credit_amount, status)
