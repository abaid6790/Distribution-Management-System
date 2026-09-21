# Changelog

All notable changes to this project, by phase. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/).

## Security hardening — CSRF & rate limiting

### Added
- CSRF protection (Flask-WTF) on every form in the application —
  auto-inserted across all 20 templates that contain a POST form.
- Rate limiting (Flask-Limiter) on `/login` (10/minute/IP) and
  `/account/change-password` (15/hour), plus a generous global default
  (1000/hour/IP) on everything else. Dedicated "too many attempts" page
  instead of a raw 429.
- Friendly redirect + flash message on CSRF failure instead of a raw
  400 error page.

### Notes
- Rate limiting uses in-memory storage by default — fine for a single
  process, but needs a shared backend (Redis) once running multiple
  gunicorn workers in production. See `SECURITY.md`.

## Phase 9 — Role-based permissions

### Added
- Per-user, per-module permission system (~20 modules), editable by an
  admin independent of role.
- `Users` screen (admin-only): create logins tied to employees, assign
  role + permissions, reset passwords.
- Auto-generated one-time passwords for new/reset logins; never emailed
  or stored in plaintext.
- Forced password change on first login and after a password reset.
- Self-service "change password" available to every user at any time.
- `email` field added to the Employee model/form/list.
- Last-active-admin protection (can't demote or deactivate the only
  admin).
- Centralized access enforcement via a single `before_request` hook +
  permission-aware sidebar filtering.

### Fixed
- Database migration for the new columns now includes proper
  `server_default` values — the original generated migration would have
  failed on any database that already had users in it.

## Phase 8 — Admin

### Added
- Central `Invoices` module listing every document type with search and
  filter.
- Printable views for sales, purchases, sale returns, purchase returns,
  and payment receipts, respecting Printing Settings (paper size,
  margins, visibility toggles).
- Backup: full JSON export of all business data, downloadable, with
  history.
- Restore: replace all data from an uploaded backup file, confirmation
  required.
- Danger Zone: permanent reset of business data; user logins and settings
  are preserved.

### Fixed
- Danger Zone reset originally failed with a foreign-key violation
  (`transactions` deleted after the records it references instead of
  before) — corrected the delete order.
- Restore originally failed because the backup-history table references
  `users`, which restore wipes — backup history is now cleared as part of
  the wipe instead of blocking it.
- Removed an unauthorized public self-registration + email-verification
  feature that had been added to the codebase outside of any requested
  scope, including an unsafe "first registrant becomes admin" behavior.
  Fully reverted to the tested Phase 1–7 state before Phase 8 began.

## Phase 7 — Operations

### Added
- Edit and delete for Sales and Purchases, with full cascading
  recalculation of stock, cash, and totals (nothing is cached, so this
  falls out of the existing single-source-of-truth design rather than
  needing bespoke resync logic).
- Guardrails: editing/deleting a Sale or Purchase with a Return recorded
  against it is blocked; reducing or deleting a Purchase is blocked if it
  would push any product's stock negative because of sales that happened
  afterward.
- Stock Adjustments module (damaged/lost/broken/physical-count/
  correction/other), blocked from decreasing stock below zero.
- Opening Balances: Opening Stock, Opening Debtors, Opening Creditors —
  wired into the same stock/balance calculations as everything else.

## Phase 6 — Intelligence

### Added
- Stock module: full purchased/sold/returned/remaining breakdown per
  product.
- Low Stock view.
- Profit & Loss: Net Sales − Cost of Goods Sold − Expenses, with COGS
  valued at each product's weighted-average historical purchase cost.
- Reports: Sales, Purchases, Sale Returns, Purchase Returns, Expenses
  (date-ranged: Today/Yesterday/This Month/This Year/Custom), plus
  Debtors, Creditors, and Stock snapshots.
- Load Card: a day's sales grouped by customer and product, printable.

## Phase 5 — Money

### Added
- Debtors / Creditors pages with real outstanding-balance calculation
  (credit − returns − payments), shared by the dashboard, the Customers/
  Suppliers lists, and these dedicated pages.
- Customer payment / supplier payment recording, validated against the
  actual outstanding balance.
- Expenses module, categorized, posting to the cash book.
- Cash Book: full transaction ledger with a running balance and filters.

## Phase 4 — Returns

### Added
- Sale Returns and Purchase Returns: search the original invoice, return
  against remaining returnable quantity (accounting for prior returns),
  automatic stock and cash reversal.

## Phase 3 — Core transactions

### Added
- Stock calculation engine (single source of truth for current stock).
- Atomic, race-safe invoice numbering.
- Purchases: supplier auto-created/matched, existing-or-new product per
  line, cash ledger integration.
- Sales: customer auto-created/matched, box-or-pack line items, hard
  stock validation before write.
- Customers / Suppliers pages, auto-populated from transactions.

## Phase 2 — Master data

### Added
- Products (box/pack pricing, auto-calculated pack price).
- Employees.
- Business / Invoice Numbering / Printing settings.

## Phase 1 — Foundation

### Added
- Full 24-table data model.
- Session-based authentication.
- Dashboard shell with live KPI queries.

---

## Stack note

Originally built on Next.js/React; rebuilt from scratch on Flask +
PostgreSQL + server-rendered Jinja2 at the project owner's request, with
the same tested business logic (stock engine, invoice numbering,
find-or-create identity rules, payment resolution) ported over rather
than re-derived. All phase numbering above refers to the Flask version.
