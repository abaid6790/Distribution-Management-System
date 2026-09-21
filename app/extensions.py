from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = None

csrf = CSRFProtect()

# In-memory storage is fine for a single-process deployment. If you run
# multiple gunicorn workers/processes in production, point this at Redis
# instead (e.g. storage_uri="redis://localhost:6379") so all workers share
# the same rate-limit counters — see DEPLOYMENT.md.
limiter = Limiter(key_func=get_remote_address, default_limits=["1000 per hour"])
