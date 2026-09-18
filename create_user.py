import sys
from dotenv import load_dotenv
load_dotenv()

from werkzeug.security import generate_password_hash
from app import create_app
from app.extensions import db
from app.models import User, Employee

app = create_app()

def create_user(username, password, full_name, role="SALESMAN"):
    with app.app_context():
        if User.query.filter_by(username=username).first():
            print(f"User '{username}' already exists.")
            return

        employee = Employee(employee_code=f"EMP-{User.query.count()+1:04d}", name=full_name)
        db.session.add(employee)
        db.session.flush()

        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            full_name=full_name,
            role=role,
            employee_id=employee.id,
        )
        db.session.add(user)
        db.session.commit()
        print(f"Created user '{username}' with role {role}.")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python create_user.py <username> <password> <full name> [role]")
        sys.exit(1)
    role = sys.argv[4] if len(sys.argv) > 4 else "SALESMAN"
    create_user(sys.argv[1], sys.argv[2], sys.argv[3], role)