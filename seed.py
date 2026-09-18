from dotenv import load_dotenv

load_dotenv()

from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import User, Employee, BusinessSettings, InvoiceSettings, PrintingSettings

app = create_app()

with app.app_context():
    print("Seeding database...")

    if not User.query.filter_by(username="admin").first():
        employee = Employee(employee_code="EMP-0001", name="System Admin")
        db.session.add(employee)
        db.session.flush()

        user = User(
            username="admin",
            password_hash=generate_password_hash("admin123"),
            full_name="System Admin",
            role="ADMIN",
            employee_id=employee.id,
        )
        db.session.add(user)
        print("Created default admin user -> username: admin / password: admin123")
    else:
        print("Admin user already exists, skipping.")

    if not BusinessSettings.query.get("singleton"):
        db.session.add(BusinessSettings(id="singleton"))
        print("Created default business settings.")

    if not InvoiceSettings.query.get("singleton"):
        db.session.add(InvoiceSettings(id="singleton"))
        print("Created default invoice settings.")

    if not PrintingSettings.query.get("singleton"):
        db.session.add(PrintingSettings(id="singleton"))
        print("Created default printing settings.")

    db.session.commit()
    print("Seed complete.")
