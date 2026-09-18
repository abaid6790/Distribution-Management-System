"""
Identity rule: same name + phone + address => same customer/supplier. Any
difference in phone or address (with the same name) creates a new record.
"""

from app.extensions import db
from app.models import Customer, Supplier


def find_or_create_customer(name: str, phone: str, address: str) -> Customer:
    name, phone, address = name.strip(), phone.strip(), address.strip()

    existing = (
        Customer.query.filter_by(name=name, phone=phone, address=address).first()
    )
    if existing:
        return existing

    customer = Customer(name=name, phone=phone, address=address)
    db.session.add(customer)
    db.session.flush()
    return customer


def find_or_create_supplier(name: str, phone: str, address: str) -> Supplier:
    name, phone, address = name.strip(), phone.strip(), address.strip()

    existing = (
        Supplier.query.filter_by(name=name, phone=phone, address=address).first()
    )
    if existing:
        return existing

    supplier = Supplier(name=name, phone=phone, address=address)
    db.session.add(supplier)
    db.session.flush()
    return supplier
