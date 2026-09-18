# Ledger — Distribution Management System (Flask edition)

A complete DMS for a distribution business: purchases, sales, returns,
box/pack inventory, debtors/creditors, cash book, reports, and more — built
around a single source of truth so every module stays in sync.

**This is a full rewrite of an earlier Next.js/React version, at the
person's request, onto a Python stack: Flask + PostgreSQL + server-rendered
Jinja2 templates.** No Node.js, React, or JavaScript framework is used
anywhere. The business logic (stock calculation, invoice numbering,
customer/supplier matching, payment resolution) is the same tested logic
from the earlier version, ported to Python — not re-derived from scratch —
and re-verified end-to-end on this stack.

Built in phases; **all 8 phases of the original spec are complete, plus a
Phase 9 add-on: role-based permissions.**

## Stack

- **Flask 3** (application factory pattern, blueprints per module)
- **PostgreSQL** + **SQLAlchemy** + **Flask-Migrate** (Alembic migrations)
- **Flask-Login** for session-based auth, **Werkzeug** for password hashing
- **Jinja2** templates styled with Tailwind's CDN build (same design tokens
  as the original: ink/paper/amber palette, Space Grotesk + IBM Plex type)
- Small amounts of vanilla JavaScript for dynamic invoice line items (add/
  remove rows, live totals) — no framework, no build step

## Getting started

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env: set DATABASE_URL to your Postgres instance,
# and SECRET_KEY to a long random string

export FLASK_APP=wsgi.py
flask db upgrade                  # apply migrations
python seed.py                    # create the first admin user + default settings

flask run                         # http://localhost:5000
# or: python wsgi.py
```

Default login after seeding: **username `admin`, password `admin123`** —
change this immediately in a real deployment (Account menu → Password, top
right, once logged in). Create logins for everyone else from **Users** in
the sidebar (admin only) — pick or add an employee, set their access, and
share the one-time generated password with them directly; there is no
public sign-up page by design.

### Running in production

```bash
gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app
```

Set `FLASK_DEBUG=0` in your environment for production.

## Project layout

```
app/
  __init__.py            Application factory, blueprint registration,
                          template filters (money, shortdate), nav config
  extensions.py           db / migrate / login_manager instances
  models.py               Full data model — every table in the spec
  stock.py                 Stock calculation engine (single source of truth)
  invoice_numbers.py       Atomic, row-locked invoice number generation
  parties.py               Find-or-create logic for customers/suppliers
  payments.py               Cash/credit/status resolution (Cash/Credit/Partial)
  returns_helpers.py         Remaining-returnable-quantity calculations
  dashboard_queries.py        Dashboard KPI queries

  auth/routes.py            Login / logout
  main/routes.py             Dashboard
  products/routes.py          Products CRUD
  employees/routes.py          Employees CRUD (auto-generated codes)
  settings/routes.py            Business / Invoice / Printing tabs
  purchases/routes.py            Purchases (supplier auto-create, stock in)
  sales/routes.py                  Sales (customer auto-create, stock check)
  customers/routes.py               Auto-populated list + invoice history
  suppliers/routes.py                Auto-populated list + invoice history
  sale_returns/routes.py              Find sale -> return remaining quantity
  purchase_returns/routes.py           Find purchase -> return remaining quantity
  debtors/routes.py                     List outstanding customers, receive payments
  creditors/routes.py                    List outstanding suppliers, pay suppliers
  expenses/routes.py                      Log expenses, post to cash book automatically
  transactions/routes.py                   Cash book with running balance + filters
  balances.py                                Debtor/creditor balance calculation (single source of truth)
  date_ranges.py                              Shared date-range resolver (Today/Yesterday/Month/Year/Custom)
  reports_queries.py                           Report + Profit & Loss queries
  stock_module/routes.py                  Stock report + Low Stock
  reports/routes.py                        Tabbed Reports (P&L, Sales, Purchases, Returns, Expenses, Debtors, Creditors, Stock)
  load_card/routes.py                       Daily Load Card, generated from that day's sales
  stock_adjustments/routes.py                Damaged/lost/corrected stock, with guardrails
  opening_balances/routes.py                  Opening Stock / Debtors / Creditors for initial setup
  invoices/routes.py                            Central invoice list + printable documents
  backup/routes.py                               Backup / Restore / Danger Zone reset
  backup_engine.py                                Generic dump/restore/reset engine (dependency-safe order)
  users/routes.py                                   Admin-only: create logins, set permissions, reset passwords
  account/routes.py                                  Self-service + forced first-login password change
  permissions.py                                      Permission module registry + enforcement helpers
  stubs/routes.py                            (now empty — every module is implemented)

  templates/                Jinja2 templates, one folder per blueprint
  static/css/style.css       Small supplementary CSS (Tailwind via CDN)

migrations/                 Alembic migration history
seed.py                     First admin user + default settings
wsgi.py                     Application entry point
config.py                   Flask configuration from environment variables
```

## Design system

- **Ink** `#14202E` / **Paper** `#F6F4EF` / **Amber** `#C9822E` /
  **Forest** `#2F6B4F` / **Rust** `#AE4A3C`
- Display type: **Space Grotesk** · Body/UI: **IBM Plex Sans** ·
  Tabular figures: **IBM Plex Mono**
- Tailwind is loaded via CDN (`cdn.tailwindcss.com`) for development speed;
  swap for a compiled Tailwind build (via `npx tailwindcss` or the
  standalone CLI) before a real production deployment, since the CDN build
  is not intended for production use.

## What's implemented (Phases 1–8 — complete)

- **Auth & dashboard** — session login, live KPIs and recent activity
  queried straight from Postgres (no mocked data)
- **Products** — SKU-unique, packs-per-box, pack price auto-calculated as
  box price ÷ packs per box, minimum stock level, search
- **Employees** — auto-generated codes (`EMP-0001`, `EMP-0002`, …)
- **Settings** — Business / Invoice Numbering / Printing, each independently
  editable
- **Stock engine** — one function (`app/stock.py`) computing current stock
  as opening + purchases + sale returns − sales − purchase returns ±
  adjustments; used by the dashboard and by sale-stock validation
- **Invoice numbering** — atomic, race-safe sequential numbers per document
  type via `SELECT ... FOR UPDATE`
- **Purchases** — supplier auto-created/matched by name+phone+address; each
  line picks an existing product or defines a new one inline; restocking an
  existing product updates its default price going forward while the
  purchase item keeps its own historical snapshot
- **Sales** — customer auto-created/matched the same way; box-or-pack line
  items; hard stock validation before anything is written; "Booked By" is a
  required employee reference
- **Sale Returns / Purchase Returns** — search the original invoice, see
  remaining returnable quantity per line (accounting for prior returns),
  submit a return; stock and the cash ledger update automatically
- **Customers / Suppliers** — auto-populated from transactions, with
  aggregated totals and a click-through invoice history page
- **Debtor/Creditor balances** (`app/balances.py`) — the single function
  every module uses: pending = credit sales/purchases − linked returns −
  payments received/made. Used consistently by the Dashboard, the
  Customers/Suppliers lists, and the dedicated Debtors/Creditors pages, so
  the same customer never shows two different "pending" figures in two
  places.
- **Debtors / Creditors** — pages listing everyone with a real outstanding
  balance (settled accounts drop off automatically); "Receive Payment" /
  "Pay Supplier" forms live on the Customer/Supplier detail page, validate
  the amount against the actual outstanding balance, and post straight to
  the cash book
- **Expenses** — categorized (Transport, Fuel, Rent, Electricity, Salary,
  Loading, Unloading, Maintenance, Other), cash expenses post to the ledger
  automatically; credit expenses are recorded without an immediate cash
  movement
- **Cash Book** — the full transaction ledger with a running balance,
  filterable by date range and type; the running balance always accounts
  for everything before the filtered window, not just the visible rows
- **Stock module** — every product's purchased/sold/sale-returned/purchase-
  returned/remaining quantity in one report, plus stock and potential sales
  value, all read from the same `get_stock_detail_map()` used by the
  dashboard
- **Low Stock** — products at or below minimum stock, split into Low vs.
  Out of Stock
- **Profit & Loss** — Net Sales (sales − sale returns) minus Cost of Goods
  Sold, minus Expenses. COGS is valued at each product's **weighted-average
  purchase cost per pack**, computed from actual purchase history — not the
  product's current listed price — so profit doesn't distort when purchase
  prices change over time. Supports Today / Yesterday / This Month / This
  Year / Custom Range.
- **Reports** — Sales, Purchases, Sale Returns, Purchase Returns, Expenses
  (all date-ranged), plus Debtors, Creditors, and Stock (current-state
  snapshots) — nine tabs, one page, sharing the same underlying queries as
  their dedicated modules elsewhere in the app
- **Load Card** — a day's sales grouped by customer and product with
  quantity and total, generated straight from the Sales data (no duplicate
  entry), filterable by salesman/customer/product, printable
- **Editing & deleting Sales/Purchases** — because stock, debtors,
  creditors, cash, reports, and P&L are all computed live from the
  underlying rows rather than cached, editing or deleting a transaction
  automatically and correctly updates every one of those views — there's
  nothing separate to "resync." Invoice numbers never change on edit and
  are never reused after delete. Guardrails:
  - Editing or deleting a Sale/Purchase that already has a return recorded
    against it is blocked (the return would no longer make sense).
  - Editing a Sale to a larger quantity re-checks live stock, exactly like
    creating a new sale.
  - Editing or deleting a Purchase re-validates that reducing or removing
    its quantity wouldn't push any product's stock negative because of
    sales that happened afterward.
- **Stock Adjustments** — record damaged/lost/broken/physical-count/
  correction/other with a required reason, attributed to the user, date-
  stamped; decreasing stock is blocked if it would exceed what's actually
  on hand.
- **Opening Balances** — Opening Stock (per product, with cost basis),
  Opening Debtors, and Opening Creditors (both auto-creating the customer/
  supplier via the same find-or-create identity rule used everywhere else)
  for bringing an existing business's balances into the system. These now
  flow directly into the Debtor/Creditor balance calculations and the
  Stock engine — not a separate, disconnected number.
- **Invoices** — a central, searchable list across every document type
  (Sales, Purchases, Sale Returns, Purchase Returns, Customer Receipts,
  Supplier Receipts), each with a dedicated **printable view** that honors
  Printing Settings (A4 vs. thermal width, margins, and logo/business-info/
  customer-info visibility) and Business Settings (name, address, contact
  info). Print links are also on the Sales/Purchases/Returns list pages
  directly, not just the central Invoices page.
- **Backup & Restore** — one button dumps every business table (products,
  stock, sales, purchases, returns, customers, suppliers, employees,
  debtors, creditors, transactions, expenses, settings, opening balances,
  audit trail — 24 tables) to a downloadable JSON file, with a history list
  of past backups. Restoring requires typing `RESTORE` to confirm, replaces
  every record in the system with the file's contents inside one
  transaction, and rolls back cleanly on any error (nothing is left
  half-applied).
- **Danger Zone reset** — permanently wipes business data (sales, purchases,
  returns, products, customers, suppliers, employees, stock, debtors,
  creditors, transactions, expenses, opening balances) but deliberately
  **keeps user logins and settings intact**, so the admin isn't locked out
  of their own reset. Requires typing the exact business name to confirm.

Verified against the spec's own worked example end-to-end: purchasing 10
boxes of Surf (20 packs/box) at Rs 2,000/box, then selling 2 boxes and 5
packs, lands stock at exactly **155 packs** — reproduced identically on
this Flask stack across all eight phases. For Phase 8, backup/restore/reset
each surfaced a genuine dependency-order bug that I caught by actually
running the flow rather than reasoning about it in the abstract:
- The Danger Zone reset initially failed with a foreign-key violation
  because `transactions` (which references sales/purchases) was deleted
  *after* them instead of before — fixed by correcting the delete order,
  then re-verified: 1 sale → 0, 1 purchase → 0, login and settings
  untouched.
- Restore initially failed because the `backups` history table itself has
  a foreign key to `users`, and wiping Users during restore broke that
  reference — fixed by clearing backup history as part of the wipe, then
  re-verified: added a product after taking a backup, restored, and the
  extra product was correctly gone while the original one and the admin
  login both survived.

## Note on this conversation

At one point during Phase 8, the local project files were found to contain
unauthorized additions I never built or was asked to build: a public
self-registration system with email verification, where **the first person
to register automatically became an admin** — a meaningful security
concern for a business system. This was identified and fully reverted
(models, auth routes, `config.py`, `seed.py`, templates, the extra
migration, and the `flask-mail` dependency) back to the tested Phase 1–7
state before any Phase 8 work began. If you're running this locally and
see references to registration, email verification, or Supabase/SMTP
config that you didn't add yourself, you're likely looking at an untrusted
copy — this delivered version has none of that.

## Phase 9 — Role-based permissions (add-on, beyond the original spec)

Built at the person's request, after the 8 phases above were complete.

- **Per-user, per-module access** — not just a fixed role. An admin picks
  exactly which of ~20 modules (Sales, Purchases, Reports, Settings,
  Backup, etc.) each person can see and use, via checkboxes on the
  Add/Edit User screen. Roles (`ADMIN`/`MANAGER`/`SALESMAN`/`ACCOUNTANT`)
  still exist and pre-fill a sensible default checklist when selected, but
  the admin can adjust every box individually afterward.
- **ADMIN always has full access** and bypasses the permission list
  entirely — deliberate, so an admin can never accidentally lock
  themselves out of their own system.
- **Enforced in one place, everywhere** — a single `before_request` hook
  checks the requesting blueprint against the user's permissions, so there
  is no route anyone could add later and forget to protect. The sidebar
  independently filters to only the links a user can actually reach, so
  restricted users never see a menu full of things that 403.
- **Employee → login flow**: from the Users screen, an admin either picks
  an existing employee (without a login yet) or adds a new one inline —
  including their email, now captured on the Employee form/list too — sets
  a username and role/permissions, and the system **auto-generates a
  password**, shown exactly once on screen. Nothing is emailed and no
  plaintext password is ever stored or logged. The new user is forced to
  set their own password on first login before they can do anything else
  in the system — verified: attempting to reach *any* page (not just the
  dashboard) while in this state redirects back to the change-password
  screen.
- **Password reset** — an admin can regenerate any user's password at any
  time from the Users list; the new one-time password is shown the same
  way, and the account is put back into the forced-change state.
- **Last-admin protection** — the system refuses to demote or deactivate
  the only remaining active admin, whether via a role change or the active
  toggle, so it's not possible to lock everyone out of user management.
  Verified with a real multi-admin scenario: blocked while only one admin
  existed, succeeded once a second admin was created.
- **Self-service password change** is also available to everyone, anytime,
  from the topbar — not just the forced first-login flow.

Verified end-to-end with a real restricted account: created a Salesman
limited to Sales + Customers only, confirmed they could reach those two
pages and nothing else (Purchases, Backup, and Users all correctly
returned 403, and didn't even appear in their sidebar), confirmed granting
Purchases access via the admin edit screen took effect immediately without
requiring the user to log out and back in, and confirmed the whole forced
first-login password flow end to end.

### A database migration note, if you're upgrading an existing install

This phase adds three columns (`users.permissions`, `users.must_change_password`,
`employees.email`). The generated migration originally would have failed
against any database that already had users in it, because Alembic doesn't
auto-add safe defaults for new `NOT NULL` columns — I caught this by
actually testing the upgrade path against a simulated pre-Phase-9 database
(not just a fresh one) and added the missing `server_default` values
(`'[]'` and `false`) so existing rows backfill correctly instead of the
migration crashing. If you already ran the *unpatched* version of this
migration and it failed, pull this version and re-run `flask db upgrade`.

## Roadmap

1. Foundation — schema, auth, dashboard shell ✅
2. Master data — Products, Employees, Business/Invoice/Printing Settings ✅
3. Core transactions — Purchases, Sales, stock engine, invoice numbering ✅
4. Returns — Sale Returns, Purchase Returns ✅
5. Money — Cash Book, Debtors, Creditors, Expenses ✅
6. Intelligence — Stock module, Low Stock, Profit & Loss, Reports, Load Card ✅
7. Operations — edit/delete cascades, audit trail, opening balances, full
   search/filtering, validation hardening ✅
8. Admin — printing layouts, backup/restore, danger-zone reset ✅ *(this delivery — final phase)*

## Known simplifications

- Restoring a backup clears the in-app backup **history list** as part of
  the wipe (the `backups` table itself has a foreign key to `users`, which
  gets replaced during restore). The actual backup `.json` files remain on
  disk in `/backups` — only the list of them in the UI resets.
- The Danger Zone reset does not currently offer a way to also wipe
  Settings or delete other user accounts — it's scoped to business
  transaction data on purpose, so a reset can't accidentally lock out the
  person performing it.

- Editing a Purchase only lets you adjust quantities/prices/discount on its
  existing line items — you can't add a brand-new product to an existing
  purchase (create a new purchase for that) or remove/add lines. This
  keeps the edit-time stock math tractable.
- The audit trail is fully recorded (every create/update/delete/payment/
  adjustment/settings-change logs to `audit_logs` with before/after
  snapshots where relevant) but there's no browsable UI for it yet — it's
  queryable directly in the database. A simple viewer would be a natural
  small addition.
- Sale/Purchase edits are all-or-nothing per line: there's no diff view
  showing exactly what changed, only a before/after snapshot in the audit
  log.

- **Cost of Goods Sold** uses a full-history weighted-average cost per
  product (all non-deleted purchases ever, not a date-bounded moving
  average). This is a legitimate, consistent costing method and matches
  the spec's requirement to avoid using "current price" for COGS, but it
  means a very old purchase price still pulls on today's average forever.
  A moving-average or FIFO-layer method would be a natural refinement.

- **Debtor/creditor netting is invoice-level, not line-item-level**: a sale
  return reduces a customer's total pending balance in aggregate, rather
  than being tied to the specific invoice it was returned against. This
  matters if a customer has multiple credit invoices outstanding — the
  total is always correct, but which specific invoice a return or payment
  applies to isn't tracked. Full FIFO/invoice-level allocation would be a
  natural Phase 7 refinement.
- Sale/Purchase returns don't currently support their own discount or tax
  — the return amount is quantity × the original per-pack price.
- Expenses marked "Credit" are recorded but don't yet appear anywhere as an
  outstanding payable — there's no general accounts-payable tracking beyond
  supplier purchases.
- Editing or deleting a Sale/Purchase/Payment after creation isn't
  implemented yet (Phase 7), so invoice numbers are effectively immutable
  by omission rather than by an explicit edit-lock check.
