from flask import Blueprint, render_template
from flask_login import login_required

stubs_bp = Blueprint("stubs", __name__)

STUBS = []


def _make_view(title, phase, description):
    @login_required
    def view():
        return render_template("stub.html", title=title, phase=phase, description=description)

    return view


for path, title, phase, description in STUBS:
    endpoint = path.strip("/").replace("/", "_") or "root"
    stubs_bp.add_url_rule(path, endpoint=endpoint, view_func=_make_view(title, phase, description))
