<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&height=250&color=0:14202E,50:C9822E,100:2F6B4F&text=LEDGER&fontSize=65&fontColor=F6F4EF&fontAlignY=38&desc=Distribution%20Management%20System&descSize=20&descAlignY=62&animation=fadeIn" width="100%"/>

<br>

<img src="https://readme-typing-svg.demolab.com?font=Space+Grotesk&weight=600&size=22&duration=3000&pause=1000&color=C9822E&center=true&vCenter=true&width=850&lines=One+Source+of+Truth+for+Distribution+Management;Sales+%7C+Purchases+%7C+Inventory+%7C+Accounts;Flask+%2B+PostgreSQL+%2B+Jinja2;Role-Based+Permissions+%7C+Reports+%7C+Backup+%7C+Audit+Trail" alt="Typing SVG"/>

<br>

![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge\&logo=python\&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3-000000?style=for-the-badge\&logo=flask\&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge\&logo=postgresql\&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-ORM-D71F00?style=for-the-badge)
![Jinja2](https://img.shields.io/badge/Jinja2-Templates-B41717?style=for-the-badge)
![Alembic](https://img.shields.io/badge/Alembic-Migrations-1F6FEB?style=for-the-badge)

<br>

[![GitHub Stars](https://img.shields.io/github/stars/abaid6790/Ledger?style=flat-square)](https://github.com/abaid6790/Ledger)
[![GitHub Forks](https://img.shields.io/github/forks/abaid6790/Ledger?style=flat-square)](https://github.com/abaid6790/Ledger)
[![GitHub Issues](https://img.shields.io/github/issues/abaid6790/Ledger?style=flat-square)](https://github.com/abaid6790/Ledger)
[![Last Commit](https://img.shields.io/github/last-commit/abaid6790/Ledger?style=flat-square)](https://github.com/abaid6790/Ledger)

<br>

### 📦 Distribution Management · 💰 Accounting · 📊 Reporting · 🔐 Access Control

</div>

---

# ⚡ What is Ledger?

**Ledger** is a complete **Distribution Management System (DMS)** built for businesses that purchase, stock, distribute, and sell products in **boxes and individual packs**.

It brings the entire business workflow into one connected system:

```text
┌──────────────┐
│   PURCHASE   │
└──────┬───────┘
       ↓
┌──────────────┐
│    STOCK     │
└──────┬───────┘
       ↓
┌──────────────┐
│     SALE     │
└──────┬───────┘
       ↓
┌───────────────────────────────┐
│ Stock │ Cash │ Debtors │ P&L │
└───────────────────────────────┘
```

The system is designed around a **single source of truth**, meaning stock, balances, cash, reports, and profit are calculated from the underlying transaction data rather than maintaining disconnected copies of the same information.

---

# 🧠 Engineering Philosophy

> **Enter the transaction once. Let every dependent module calculate from it.**

A sale should not require manually updating:

* Stock
* Customer balance
* Cash
* Reports
* Profit
* Load Card

Instead:

```text
                    SALE
                     │
       ┌─────────────┼─────────────┐
       ↓             ↓             ↓
     STOCK         MONEY        REPORTS
       │             │             │
       ↓             ↓             ↓
   Inventory      Cash/Debt     P&L / Sales
```

This architecture significantly reduces synchronization problems between modules.

---

# 🔥 Highlights

<table>
<tr>
<td width="50%">

### 📦 Inventory

* Box / pack inventory
* Central stock engine
* Opening stock
* Stock adjustments
* Low-stock alerts
* Sale returns
* Purchase returns
* Stock validation

</td>

<td width="50%">

### 💵 Financials

* Cash Book
* Debtors
* Creditors
* Payments
* Expenses
* Profit & Loss
* Weighted-average COGS
* Opening balances

</td>
</tr>

<tr>
<td>

### 🧾 Transactions

* Sales
* Purchases
* Returns
* Invoice numbering
* Customer matching
* Supplier matching
* Printable invoices
* Transaction editing

</td>

<td>

### 🔐 Administration

* User management
* Roles
* Per-module permissions
* Password reset
* Forced password change
* Backup / Restore
* Danger Zone reset
* Audit trail

</td>
</tr>
</table>

---

# 🏗️ Architecture

```text
                         ┌───────────────────────┐
                         │        Browser        │
                         │                       │
                         │ Jinja2 + Tailwind CSS │
                         │ + Vanilla JavaScript  │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │       Flask 3         │
                         │ Application Factory   │
                         │      + Blueprints     │
                         └───────────┬───────────┘
                                     │
             ┌───────────────────────┼────────────────────────┐
             │                       │                        │
             ▼                       ▼                        ▼
      ┌──────────────┐       ┌──────────────┐        ┌──────────────┐
      │ Transactions │       │ Business     │        │ Auth &       │
      │              │       │ Logic        │        │ Permissions  │
      │ Sales        │       │              │        │              │
      │ Purchases    │       │ Stock        │        │ Users        │
      │ Returns      │       │ Balances     │        │ Roles        │
      └──────┬───────┘       │ Payments     │        │ Permissions  │
             │               └──────┬───────┘        └──────────────┘
             │                      │
             └──────────────┬───────┘
                            ▼
                   ┌──────────────────┐
                   │    SQLAlchemy    │
                   │       ORM        │
                   └────────┬─────────┘
                            ▼
                   ┌──────────────────┐
                   │   PostgreSQL     │
                   │                  │
                   │ Single Source    │
                   │   of Truth       │
                   └──────────────────┘
```

---

# 🛠️ Technology Stack

| Technology                     | Purpose                      |
| ------------------------------ | ---------------------------- |
| 🐍 **Python**                  | Application language         |
| 🌶️ **Flask 3**                | Web framework                |
| 🐘 **PostgreSQL**              | Primary database             |
| 🧱 **SQLAlchemy**              | ORM                          |
| 🔄 **Flask-Migrate / Alembic** | Database migrations          |
| 🔐 **Flask-Login**             | Session authentication       |
| 🔑 **Werkzeug**                | Password hashing             |
| 🧩 **Jinja2**                  | Server-side templates        |
| 🎨 **Tailwind CSS**            | UI styling                   |
| ⚡ **Vanilla JavaScript**       | Dynamic invoice interactions |
| 🚀 **Gunicorn**                | Production WSGI server       |

### No frontend framework

This version deliberately does **not** use:

```text
❌ React
❌ Next.js
❌ Node.js
❌ Frontend build framework
```

The application uses:

```text
Flask
+
Jinja2
+
Tailwind
+
Small amounts of Vanilla JavaScript
```

This is a full rewrite of an earlier Next.js/React implementation onto a Python server-rendered architecture.

The business logic for stock calculation, invoice numbering, party matching, and payment resolution was ported and re-verified rather than re-derived from scratch.

---

# 📦 Core Modules

```text
Dashboard
Products
Employees
Purchases
Sales
Customers
Suppliers
Sale Returns
Purchase Returns
Debtors
Creditors
Expenses
Cash Book
Stock
Stock Adjustments
Opening Balances
Reports
Load Card
Invoices
Users
Account
Settings
Backup & Restore
```

---

# 📊 Business Flow

```text
                     ┌─────────────┐
                     │  PRODUCTS   │
                     └──────┬──────┘
                            │
              ┌─────────────┴─────────────┐
              ↓                           ↓
       ┌─────────────┐             ┌─────────────┐
       │  PURCHASES  │             │    SALES    │
       └──────┬──────┘             └──────┬──────┘
              │                           │
              ↓                           ↓
       ┌─────────────┐             ┌─────────────┐
       │ STOCK ↑     │             │ STOCK ↓     │
       └──────┬──────┘             └──────┬──────┘
              │                           │
              └────────────┬──────────────┘
                           ↓
                 ┌───────────────────┐
                 │ Financial Effects  │
                 ├───────────────────┤
                 │ Cash               │
                 │ Debtors/Creditors  │
                 │ Profit & Loss      │
                 │ Reports            │
                 └───────────────────┘
```

---

# 📦 Stock Engine

Stock calculation is centralized in:

```text
app/stock.py
```

The calculation is:

```text
Opening Stock
      +
Purchases
      +
Sale Returns
      -
Sales
      -
Purchase Returns
      ±
Stock Adjustments
      =
Current Stock
```

The same stock calculation is used by the dashboard, stock reports, and sale validation.

### Example

```text
Purchase:
10 boxes

Packs per box:
20

Total purchased:
200 packs

Sold:
2 boxes = 40 packs
5 packs = 5 packs

Remaining:
200 - 45

= 155 packs
```

### Verified result

```text
155 packs
```

The worked example was reproduced end-to-end on the Flask/PostgreSQL implementation.

---

# 🛒 Purchases

Purchases support:

* Supplier auto-create
* Supplier matching
* Existing products
* Inline product creation
* Box quantities
* Pack quantities
* Historical purchase prices
* Stock updates
* Cash purchases
* Credit purchases
* Purchase returns

### Historical pricing

When an existing product is restocked:

```text
Current/default price
        ↓
Updated for future purchases
```

while the original purchase line retains its own historical price snapshot.

---

# 💵 Sales

Sales support:

* Customer auto-create
* Customer matching
* Box selling
* Pack selling
* Cash
* Credit
* Partial payment
* Required **Booked By** employee
* Live stock validation
* Automatic invoice numbers
* Printable invoices

Before the sale is committed:

```text
Requested Quantity
        ↓
Current Stock
        ↓
Validation
        ↓
Allowed / Rejected
```

A sale cannot push inventory below the available stock.

---

# 🔄 Returns

## Sale Returns

```text
Original Sale
      ↓
Find Invoice
      ↓
Calculate Previously Returned Qty
      ↓
Calculate Remaining Returnable Qty
      ↓
Return
      ↓
Stock + Financial Updates
```

## Purchase Returns

```text
Original Purchase
      ↓
Find Invoice
      ↓
Calculate Previously Returned Qty
      ↓
Calculate Remaining Returnable Qty
      ↓
Return
      ↓
Stock + Financial Updates
```

Previously returned quantities are automatically taken into account.

---

# 👥 Customers & Suppliers

Customers and suppliers are automatically created or matched using:

```text
Name
+
Phone
+
Address
```

Each party can have:

* Aggregated transaction totals
* Outstanding balance
* Invoice history
* Payment history
* Related documents

---

# 💳 Debtors & Creditors

The balance calculation lives centrally in:

```text
app/balances.py
```

### Customer

```text
Credit Sales
- Sale Returns
- Payments Received
+ Opening Balance
=
Outstanding
```

### Supplier

```text
Credit Purchases
- Purchase Returns
- Payments Made
+ Opening Balance
=
Outstanding
```

The same calculation is reused across:

```text
Dashboard
Customers
Suppliers
Debtors
Creditors
Reports
```

This prevents different parts of the system from displaying different balances for the same party.

---

# 💰 Cash Book

The Cash Book provides a complete transaction ledger with:

* Running balance
* Date filtering
* Transaction filtering
* Sales
* Purchases
* Receipts
* Supplier payments
* Expenses
* Other financial movements

The running balance considers transactions occurring before the selected filter window, rather than calculating only from the visible rows.

---

# 📈 Profit & Loss

Ledger calculates:

```text
Net Sales
    ↓
Sales - Sale Returns
    ↓
- Cost of Goods Sold
    ↓
- Expenses
    ↓
Profit
```

### COGS

COGS uses:

> **Weighted-average purchase cost per pack**

calculated from actual purchase history rather than the product's current listed selling price.

Supported ranges:

```text
Today
Yesterday
This Month
This Year
Custom Range
```

---

# 📊 Reports

A unified Reports page contains:

```text
┌───────────────────────────────────────────────┐
│ P&L │ Sales │ Purchases │ Returns │ Expenses │
├───────────────────────────────────────────────┤
│ Debtors │ Creditors │ Stock                  │
└───────────────────────────────────────────────┘
```

### Reports included

* Profit & Loss
* Sales
* Purchases
* Sale Returns
* Purchase Returns
* Expenses
* Debtors
* Creditors
* Stock

The reporting layer shares the same underlying business queries used by the dedicated modules.

---

# 🚚 Daily Load Card

The Load Card is generated directly from daily sales.

```text
Sales
  ↓
Customer
  ↓
Product
  ↓
Quantity
  ↓
Total
```

No duplicate manual data entry.

Supports:

* Salesman filtering
* Customer filtering
* Product filtering
* Printable output

---

# 🧾 Invoice Management

A centralized invoice system covers:

```text
Sales
Purchases
Sale Returns
Purchase Returns
Customer Receipts
Supplier Receipts
```

Every document has a dedicated printable view.

### Printing configuration

```text
A4
Thermal
Margins
Logo visibility
Business information
Customer information
```

Print links are also available directly from transaction lists.

---

# 🔢 Atomic Invoice Numbering

Invoice numbering is implemented in:

```text
app/invoice_numbers.py
```

Numbers are generated using row locking:

```sql
SELECT ... FOR UPDATE
```

This provides race-safe sequential invoice generation when multiple requests occur concurrently.

Invoice numbers:

* Do not change during edits
* Are not reused after deletion

---

# ✏️ Transaction Editing

Sales and purchases can be edited while maintaining calculated consistency.

Because stock, balances, reports, cash, and P&L are calculated from the underlying records, changing a transaction automatically changes dependent views.

### Guardrails

A sale/purchase with an existing return cannot be edited or deleted if doing so would invalidate the return.

Increasing a sale quantity performs live stock validation again.

Reducing or deleting a purchase checks whether later sales would cause stock to become negative.

---

# 📦 Stock Adjustments

Stock adjustments support:

```text
Damaged
Lost
Broken
Physical Count
Correction
Other
```

Every adjustment requires:

* Reason
* User attribution
* Timestamp
* Quantity
* Direction

Decreasing stock beyond the available quantity is blocked.

---

# 🏁 Opening Balances

Existing businesses can initialize:

### Opening Stock

Per-product quantity and cost basis.

### Opening Debtors

Existing customer balances.

### Opening Creditors

Existing supplier balances.

Opening balances are integrated directly into the same stock and balance engines rather than stored as disconnected numbers.

---

# 🔐 Role-Based Permissions

Phase 9 adds flexible per-user access control.

### Roles

```text
ADMIN
MANAGER
SALESMAN
ACCOUNTANT
```

Roles provide default permission sets, but administrators can customize each user's permissions individually.

Example:

```text
User: Salesman

☑ Sales
☑ Customers
☑ Load Card

☐ Purchases
☐ Suppliers
☐ Reports
☐ Backup
☐ Settings
☐ Users
```

---

# 🛡️ Centralized Permission Enforcement

Permissions are enforced centrally through a request-level check.

```text
Incoming Request
       ↓
Authentication
       ↓
Permission Resolver
       ↓
┌──────┴──────┐
│             │
Allowed      Denied
│             │
↓             ↓
Route         403
```

The navigation system independently filters unavailable modules.

Therefore a restricted user:

```text
Cannot access restricted routes
AND
Does not see restricted navigation links
```

---

# 👤 User Management

Administrators can:

* Create users
* Link employees
* Add employees inline
* Assign roles
* Customize permissions
* Reset passwords
* Activate/deactivate accounts

The system generates a temporary password.

The password:

* Is displayed once
* Is not emailed
* Is never stored in plaintext
* Is not logged

---

# 🔑 First Login Security

New users are forced to change their temporary password.

```text
Account Created
      ↓
Temporary Password
      ↓
First Login
      ↓
Change Password
      ↓
Normal Access
```

The restriction applies to the entire application, not only the dashboard.

---

# 🛡️ Last Admin Protection

The application prevents the only remaining active administrator from being:

```text
Demoted
or
Deactivated
```

This protects the system from accidentally losing administrative access.

---

# 💾 Backup & Restore

The backup system exports the business database into a downloadable JSON backup.

It covers business data such as:

```text
Products
Stock
Sales
Purchases
Returns
Customers
Suppliers
Employees
Debtors
Creditors
Transactions
Expenses
Settings
Opening Balances
Audit Logs
...
```

### Restore flow

```text
Backup JSON
     ↓
Type RESTORE
     ↓
Dependency-safe wipe
     ↓
Restore inside transaction
     ↓
Validation
     ↓
COMMIT
```

If an error occurs:

```text
ROLLBACK
```

The database is not intentionally left partially restored.

---

# ☢️ Danger Zone

The Danger Zone permanently clears business data.

It removes:

```text
Sales
Purchases
Returns
Products
Customers
Suppliers
Employees
Stock
Debtors
Creditors
Transactions
Expenses
Opening Balances
```

It intentionally keeps:

```text
User Logins
Settings
```

Confirmation requires entering the exact configured business name.

---

# 🧾 Audit Trail

The system records audit events for:

```text
Create
Update
Delete
Payment
Stock Adjustment
Settings Changes
```

Where applicable, before/after snapshots are stored.

The audit data is currently queryable directly from PostgreSQL; a dedicated audit viewer is a future enhancement.

---

# 🧪 Real Verification & Bug Fixes

The system was not only implemented from the specification; important flows were actually exercised end-to-end.

### Danger Zone dependency bug

The reset process initially encountered a foreign-key dependency involving transactions referencing sales/purchases.

The deletion order was corrected so dependent records are cleared before their referenced records.

The corrected flow was re-tested:

```text
1 Sale
↓
Reset
↓
0 Sales

1 Purchase
↓
Reset
↓
0 Purchases

Login → Preserved
Settings → Preserved
```

---

### Restore dependency bug

Backup restore initially encountered a dependency involving the backup history table and users.

The restore process was corrected to clear the relevant backup history during the replacement operation.

The flow was then re-tested:

```text
Create Backup
      ↓
Add Extra Product
      ↓
Restore Backup
      ↓
Extra Product → Gone
Original Product → Restored
Admin Login → Preserved
```

---

# 🔄 Phase 9 Migration Safety

Phase 9 introduced:

```text
users.permissions
users.must_change_password
employees.email
```

The migration was tested against a simulated pre-Phase-9 database.

Safe defaults were added so existing records could be upgraded without failing on newly introduced non-null fields.

This is particularly important when upgrading an existing installation rather than creating a completely fresh database.

---

# 🔒 Authentication Security Note

During development, an unauthorized copy of the local project was found containing a public registration system.

That version included:

```text
Public Registration
Email Verification
First Registered User → Admin
SMTP Configuration
```

Those additions were not part of the intended architecture and were reverted.

The intended system uses:

```text
Admin
  ↓
Create User
  ↓
Assign Permissions
  ↓
Generate One-Time Password
  ↓
User Changes Password
```

There is intentionally **no public self-registration system**.

If an installation contains unexpected registration, email verification, Supabase, or SMTP configuration that was not intentionally added, it should be treated as a different/untrusted copy of the project.

---

# 🎨 Design System

Ledger uses a custom business-oriented visual language.

### Colors

```text
INK      #14202E
PAPER    #F6F4EF
AMBER    #C9822E
FOREST   #2F6B4F
RUST     #AE4A3C
```

### Typography

```text
Display
Space Grotesk

Body / UI
IBM Plex Sans

Numbers / Tables
IBM Plex Mono
```

The interface uses Tailwind through CDN during development.

For production, the CDN build should be replaced with a compiled Tailwind build.

---

# 📁 Project Structure

```text
Ledger/
│
├── app/
│   ├── __init__.py
│   ├── extensions.py
│   ├── models.py
│   │
│   ├── stock.py
│   ├── invoice_numbers.py
│   ├── parties.py
│   ├── payments.py
│   ├── returns_helpers.py
│   ├── balances.py
│   ├── date_ranges.py
│   ├── dashboard_queries.py
│   ├── reports_queries.py
│   ├── backup_engine.py
│   ├── permissions.py
│   │
│   ├── auth/
│   ├── main/
│   ├── products/
│   ├── employees/
│   ├── settings/
│   ├── purchases/
│   ├── sales/
│   ├── customers/
│   ├── suppliers/
│   ├── sale_returns/
│   ├── purchase_returns/
│   ├── debtors/
│   ├── creditors/
│   ├── expenses/
│   ├── transactions/
│   ├── stock_module/
│   ├── stock_adjustments/
│   ├── opening_balances/
│   ├── reports/
│   ├── load_card/
│   ├── invoices/
│   ├── backup/
│   ├── users/
│   └── account/
│
├── templates/
│   └── ...
│
├── static/
│   └── css/
│
├── migrations/
│
├── seed.py
├── config.py
├── wsgi.py
├── requirements.txt
├── .env.example
└── README.md
```

---

# 🚀 Getting Started

## 1. Clone the repository

```bash
git clone https://github.com/abaid6790/Ledger.git
cd Ledger
```

## 2. Create a virtual environment

### Windows

```powershell
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 4. Configure environment

Copy:

```text
.env.example
```

to:

```text
.env
```

Configure:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/ledger
SECRET_KEY=your-long-random-secret
```

## 5. Apply migrations

```bash
flask db upgrade
```

## 6. Create the first administrator

```bash
python seed.py
```

## 7. Start Flask

```bash
flask run
```

Or:

```bash
python wsgi.py
```

Open:

```text
http://localhost:5000
```

---

# 🔑 Development Login

After running the seed script:

```text
Username: admin
Password: admin123
```

⚠️ Change this password immediately outside local development.

Additional users are created through:

```text
Users → Add User
```

There is no public registration page by design.

---

# 🚀 Production

Production WSGI server:

```bash
gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app
```

Set:

```env
FLASK_DEBUG=0
```

For production frontend assets, replace the Tailwind CDN build with a compiled Tailwind build.

---

# 🗺️ Project Roadmap

```text
Phase 1  Foundation
         ████████████████████ 100% ✅

Phase 2  Master Data
         ████████████████████ 100% ✅

Phase 3  Core Transactions
         ████████████████████ 100% ✅

Phase 4  Returns
         ████████████████████ 100% ✅

Phase 5  Money & Accounts
         ████████████████████ 100% ✅

Phase 6  Intelligence
         ████████████████████ 100% ✅

Phase 7  Operations
         ████████████████████ 100% ✅

Phase 8  Administration
         ████████████████████ 100% ✅

Phase 9  Role-Based Permissions
         ████████████████████ 100% ✅
```

### Completed

**9 development phases implemented.**

---

# 📸 Screenshots

Place screenshots inside:

```text
screenshots/
```

Recommended structure:

```text
screenshots/
├── dashboard.png
├── products.png
├── sales.png
├── purchases.png
├── stock.png
├── customers.png
├── suppliers.png
├── cash-book.png
├── reports.png
├── invoices.png
└── users.png
```

Then display them like:

```html
<div align="center">

<img src="screenshots/dashboard.png" width="92%">

<br><br>

<img src="screenshots/sales.png" width="92%">

<br><br>

<img src="screenshots/reports.png" width="92%">

</div>
```

---

# ⚠️ Known Simplifications

<details>
<summary><b>Backup History</b></summary>

Restoring a backup clears the in-app backup history because the `backups` table has a foreign key relationship with users.

The actual JSON backup files remain on disk.

</details>

<details>
<summary><b>Danger Zone</b></summary>

The reset operation currently clears business transaction data while intentionally keeping settings and user accounts.

</details>

<details>
<summary><b>Purchase Editing</b></summary>

Existing purchase lines can have quantities, prices and discounts adjusted.

New products cannot currently be added as new lines during purchase editing.

</details>

<details>
<summary><b>Audit Trail UI</b></summary>

The audit trail is fully recorded, but there is currently no dedicated browser UI for viewing audit records.

The records remain queryable directly from the database.

</details>

<details>
<summary><b>Sale / Purchase Edit History</b></summary>

Changes are stored through before/after audit snapshots, but there is no dedicated visual diff interface yet.

</details>

<details>
<summary><b>COGS Method</b></summary>

COGS uses full-history weighted-average purchase cost across non-deleted purchases.

A moving-average or FIFO layer system could be added as a future refinement.

</details>

<details>
<summary><b>Debtor / Creditor Allocation</b></summary>

Balance calculations are currently aggregate rather than fully allocated at invoice-line level.

A future FIFO/invoice-level allocation system could provide more granular payment and return allocation.

</details>

<details>
<summary><b>Return Pricing</b></summary>

Sale and purchase returns currently use the original per-pack price and do not have independent discount or tax fields.

</details>

<details>
<summary><b>Credit Expenses</b></summary>

Credit expenses are recorded but are not currently represented as a general accounts-payable balance.

</details>

---

# 🧭 Future Refinements

Potential future improvements include:

```text
Audit Trail Viewer
FIFO Inventory Costing
Moving-Average Costing
Invoice-Level Payment Allocation
Invoice-Level Return Allocation
Independent Return Discounts
Return Tax Handling
Credit Expense Payables
Compiled Tailwind Production Build
Advanced Analytics
```

---

# 🤝 Contributing

Contributions are welcome.

Before opening a pull request:

```text
1. Create a branch
2. Implement the change
3. Test affected business logic
4. Verify database migrations
5. Test permission boundaries
6. Check related financial calculations
7. Submit the pull request
```

See:

```text
CONTRIBUTING.md
```

for project-specific contribution guidelines.

---

# 📄 License

This project is licensed under the **MIT License**.

See:

```text
LICENSE
```

for details.

---

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&height=150&color=0:2F6B4F,50:C9822E,100:14202E&section=footer&animation=fadeIn" width="100%"/>

<br>

### ⚡ Ledger

**One source of truth for distribution management.**

<br>

Built with

**Python · Flask · PostgreSQL · SQLAlchemy · Jinja2**

<br>

![Made with Python](https://img.shields.io/badge/Made%20with-Python-3776AB?style=flat-square\&logo=python\&logoColor=white)
![Powered by Flask](https://img.shields.io/badge/Powered%20by-Flask-000000?style=flat-square\&logo=flask\&logoColor=white)
![Database PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-4169E1?style=flat-square\&logo=postgresql\&logoColor=white)

</div>
