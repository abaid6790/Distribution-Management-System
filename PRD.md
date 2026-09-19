# Product Requirements Document — Ledger (Distribution Management System)

**Status:** Implemented (Phases 1–9 complete)
**Owner:** [Your name / company]
**Last updated:** [update when you hand this to a client or investor]

---

## 1. Overview

Ledger is a web-based Distribution Management System for small and
mid-sized distribution businesses — companies that buy products from
suppliers in bulk (boxes) and resell them to customers, often by smaller
units (packs), on a mix of cash and credit terms.

It replaces manual ledgers / spreadsheets with a single system where
stock, cash, debtors, and creditors are always derived from the same
underlying transaction records — so the numbers on the dashboard, in
reports, and on a printed invoice can never quietly drift apart.

## 2. Problem statement

Distribution businesses typically track sales, purchases, stock, and
money owed/owing across separate notebooks, spreadsheets, or disconnected
software, which leads to:

- Stock counts that don't match what's actually on the shelf
- No reliable, current answer to "who owes us money, and how much"
- Manual, error-prone invoice numbering
- No audit trail of who changed what
- Difficulty producing a real Profit & Loss statement (vs. just
  purchases-minus-sales, which is not the same thing as actual profit)

## 3. Goals

- Single source of truth: stock, cash, debtors, and creditors are always
  computed from the same transaction tables, never cached/duplicated.
- Box-and-pack aware: every product can be bought and sold by box or by
  pack, with consistent, automatic unit conversion.
- Full transaction lifecycle: create, edit, delete, and return — with
  correct cascading effects on stock and money every time.
- Role-appropriate access: an owner can give staff exactly the access they
  need and nothing more.
- Auditable: every meaningful action is logged with who did it and when.
- Deployable per-client as an isolated system (see `DEPLOYMENT.md`).

## 4. Target users

| Role | Typical use |
|---|---|
| **Owner / Admin** | Full access; manages settings, users, backups, sees all reports |
| **Manager** | Day-to-day operations across most modules, minus system administration |
| **Salesman** | Records sales, manages their customers, sees the load card |
| **Accountant** | Debtors, creditors, cash book, expenses, reports |

Access per person is configured individually by an admin (see §7).

## 5. Core concepts

- **Box / Pack** — every product has a `packs_per_box` value. Purchases
  are entered in boxes (fractional boxes allowed); sales can be made by
  box or by pack. Internally everything is normalized to packs.
- **Invoice numbering** — sequential, per document type, prefix and
  padding configurable, generated atomically (never duplicated, never
  reused after a delete).
- **Find-or-create identity** — a customer or supplier is matched by
  exact name + phone + address; any difference creates a new record, so
  data entry never requires a separate "add customer" step.
- **Weighted-average costing** — Cost of Goods Sold for Profit & Loss is
  valued at each product's historical weighted-average purchase cost, not
  its current listed price.

## 6. Functional requirements (by module)

1. **Auth** — session login, forced password change on first login,
   self-service password change.
2. **Dashboard** — live KPIs (today's sales/purchases/profit/cash),
   recent activity, low stock, all computed live.
3. **Products** — SKU-unique, box/pack pricing with pack price
   auto-calculated, minimum stock level.
4. **Employees** — staff records (name, phone, address, CNIC, email),
   auto-generated employee codes.
5. **Purchases** — supplier auto-created, per-line existing-or-new
   product, edit/delete with stock-safety checks.
6. **Sales** — customer auto-created, box-or-pack line items, hard stock
   validation, edit/delete with cascading recalculation.
7. **Sale Returns / Purchase Returns** — against a specific original
   invoice, remaining-returnable-quantity enforced, reverses stock and
   cash automatically.
8. **Customers / Suppliers** — auto-populated, aggregated totals,
   invoice history.
9. **Debtors / Creditors** — real outstanding balances (credit sales/
   purchases minus returns minus payments), payment recording.
10. **Expenses** — categorized, posts to the cash book.
11. **Cash Book** — full running-balance ledger, filterable.
12. **Stock** — full purchased/sold/returned/remaining breakdown per
    product; **Low Stock** view.
13. **Reports** — Sales, Purchases, Returns, Expenses (date-ranged);
    Debtors, Creditors, Stock (point-in-time); **Profit & Loss**.
14. **Load Card** — a day's sales grouped by customer/product, printable.
15. **Stock Adjustments** — damaged/lost/broken/corrections, with a
    required reason and a hard floor at zero.
16. **Opening Balances** — opening stock, opening debtor/creditor
    balances for onboarding an existing business.
17. **Invoices** — central searchable list of every document type, with
    print views that respect Printing Settings.
18. **Backup / Restore** — full JSON export/import of all business data.
19. **Danger Zone** — permanent reset of business data, admin login and
    settings preserved.
20. **Users & Permissions** *(Phase 9)* — admin creates logins tied to
    employees, grants per-module access, resets passwords.

## 7. Roles & permissions model

- Fixed roles (`ADMIN`, `MANAGER`, `SALESMAN`, `ACCOUNTANT`) exist mainly
  as a label and a sensible starting checklist.
- The actual access control is a **per-user list of module permissions**
  (~20 modules, one roughly per sidebar item), editable individually by
  an admin regardless of the person's role label.
- `ADMIN` always has full access and cannot be permission-restricted —
  this guarantees the system can never lock every admin out of itself.
- The system will not allow the last active admin to be demoted or
  deactivated.

## 8. Non-functional requirements

- **Data integrity** — all multi-step operations (e.g. creating a sale
  and its stock/cash effects) run inside a single database transaction;
  partial writes are not possible.
- **Auditability** — create/update/delete/payment/adjustment/settings-
  change actions are logged with the acting user and a timestamp.
- **Portability** — no vendor lock-in; standard PostgreSQL, standard
  Flask, deployable on any Linux host or common PaaS.
- **Multi-tenancy** — explicitly **not** implemented; one deployment and
  one database per client business (see `DEPLOYMENT.md`).

## 9. Tech stack

Flask 3 · PostgreSQL · SQLAlchemy · Flask-Migrate (Alembic) ·
Flask-Login · Jinja2 · Tailwind CSS (CDN in dev; compile for production)
· gunicorn for production serving.

## 10. Out of scope (possible future work)

- Multi-tenant single deployment (see README "Known simplifications")
- Native mobile app (current UI is responsive web only)
- Email/SMS notifications (e.g. low-stock alerts)
- PDF export beyond browser print
- API layer for third-party integrations
- Per-invoice (rather than aggregate) debtor/creditor allocation

## 11. Glossary

- **Packs per box** — how many sellable packs make up one box of a
  product.
- **COGS** — Cost of Goods Sold; the wholesale cost of what was actually
  sold in a period, used to calculate real profit.
- **Debtor** — a customer who owes the business money (credit sales).
- **Creditor** — a supplier the business owes money to (credit purchases).
