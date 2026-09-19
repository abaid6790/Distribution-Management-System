# Contributing

This guide is for anyone (including future-you) working on this codebase.

## Local setup

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env              # then fill in DATABASE_URL and SECRET_KEY

export FLASK_APP=wsgi.py          # Windows PowerShell: $env:FLASK_APP = "wsgi.py"
flask db upgrade
python seed.py

python wsgi.py                    # http://localhost:5000, login admin / admin123
```

## Project structure

Each business module is its own Flask **blueprint** — a self-contained
folder with `routes.py`, registered in `app/__init__.py`, with templates
under `app/templates/<same_name>/`. When adding a new module, follow this
existing pattern rather than inventing a new one:

```
app/<module_name>/
  __init__.py        (empty)
  routes.py           blueprint definition + view functions
app/templates/<module_name>/
  list.html            (or index.html)
  form.html             (if it has create/edit)
```

Shared logic that multiple modules need lives at the top level of `app/`,
not inside any one blueprint — e.g. `stock.py`, `balances.py`,
`payments.py`, `parties.py`, `permissions.py`.

## Adding a new module — checklist

1. Create the blueprint folder and `routes.py` (see an existing simple
   one, e.g. `app/expenses/`, as a template).
2. Add templates under `app/templates/<module_name>/`.
3. Register the blueprint in `app/__init__.py` (import + `app.register_blueprint(...)`).
4. If it needs a new table, add the model to `app/models.py`, then:
   ```bash
   flask db migrate -m "describe the change"
   ```
   **Always open the generated migration file and check it before
   applying it** — Alembic doesn't always add safe defaults for new
   `NOT NULL` columns on tables that already have rows (this has bitten
   this project before — see the Phase 9 migration for the pattern to
   follow: `server_default=...` on new required columns).
5. Add the module to `app/permissions.py`'s `PERMISSION_MODULES` and
   `BLUEPRINT_PERMISSION_MAP` if it should be individually grantable —
   most modules should be.
6. Add it to the sidebar `nav_groups` list in `app/__init__.py`'s
   `inject_globals()`.
7. Test the migration against a database that **already has data** in it,
   not just a fresh one — this is the single most common source of bugs
   in this codebase (see `SECURITY.md` / this file's migration note).

## Conventions

- **Python**: standard PEP 8, 4-space indent. No linter is currently
  enforced in CI — running `black` and `flake8` locally before committing
  is encouraged but not required.
- **Templates**: Tailwind utility classes inline, matching the existing
  "ink / paper / amber" design tokens defined in `templates/base.html`'s
  `tailwind.config` block. Don't introduce a second design language.
- **Money**: always store as `Numeric`/`Decimal` in the database, never
  `Float`. Use the `|money` / `|money2` Jinja filters for display.
- **Dates**: form inputs are `type="date"` posting `YYYY-MM-DD` strings;
  routes parse with `datetime.strptime(date_str, "%Y-%m-%d")`. Future
  dates are rejected on every transactional form — follow the existing
  `_is_future()` helper pattern rather than reinventing it per module.
- **Stock/balance calculations**: never compute stock or debtor/creditor
  totals ad hoc in a route. Always go through `app/stock.py`
  (`get_stock_map`, `get_stock_detail_map`) and `app/balances.py`
  (`get_debtor_balances`, `get_creditor_balances`) — this is what keeps
  the dashboard, reports, and individual modules from ever disagreeing
  with each other. If a module needs a number these don't provide, add it
  there, not as a one-off query elsewhere.
- **Money-moving actions** (sales, purchases, returns, payments) must run
  inside `db.session.begin_nested()` and validate everything (stock
  availability, payment limits, etc.) before committing, following the
  existing pattern in `app/sales/routes.py` and `app/purchases/routes.py`.

## Testing changes before considering them done

There is no automated test suite yet (a good first contribution would be
adding one — pytest with a test database is the natural fit). Until then,
manually verify:

1. The happy path (create/edit/delete) via the UI or `curl`.
2. At least one validation failure (e.g. insufficient stock, invalid
   amount) and confirm the error message is clear and nothing was
   half-written to the database.
3. That a database migration applies cleanly to a database that already
   has data, not just a fresh one.
4. That the change respects the permissions system — a restricted user
   shouldn't be able to reach a new route you forgot to gate.

## Commit messages

Short, imperative, present tense: `Add stock adjustment negative-quantity guard`,
not `Added a guard` or `Fixes bug`. Reference the module/phase if useful.

## Pull requests

- Describe what changed and why, not just what.
- Call out any new database migration explicitly, and confirm you tested
  it against non-empty data (see above).
- Screenshots for anything UI-visible are appreciated but not required.
