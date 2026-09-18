<div align="center">

# ⚡ LEDGER

### Distribution Management System

**A modern, full-stack business management system for distribution operations.**

Manage **Products · Purchases · Sales · Returns · Inventory · Debtors · Creditors · Cash Flow · Reports · Users**

<br>

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:14202E,50:C9822E,100:2F6B4F&height=180&section=header&text=LEDGER&fontSize=55&fontColor=F6F4EF&animation=fadeIn&fontAlignY=35&desc=Distribution%20Management%20System&descAlignY=60&descSize=18" width="100%"/>

<br>

<img src="https://readme-typing-svg.demolab.com?font=Space+Grotesk&weight=600&size=21&duration=2800&pause=900&color=C9822E&center=true&vCenter=true&width=800&lines=One+Source+of+Truth+for+Your+Business;Inventory+%7C+Sales+%7C+Purchases+%7C+Accounts;Built+with+Flask+%2B+PostgreSQL;Role-Based+Access+%7C+Reports+%7C+Backup+%7C+Audit+Trail" alt="Typing Animation"/>

<br>

![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge\&logo=python\&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=for-the-badge\&logo=flask\&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge\&logo=postgresql\&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-ORM-D71F00?style=for-the-badge)
![Jinja2](https://img.shields.io/badge/Jinja2-Templates-B41717?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-C9822E?style=for-the-badge)

<br>

[![GitHub stars](https://img.shields.io/github/stars/abaid6790/Ledger?style=flat-square)](https://github.com/abaid6790/Ledger)
[![GitHub forks](https://img.shields.io/github/forks/abaid6790/Ledger?style=flat-square)](https://github.com/abaid6790/Ledger)
[![GitHub issues](https://img.shields.io/github/issues/abaid6790/Ledger?style=flat-square)](https://github.com/abaid6790/Ledger/issues)
[![Last Commit](https://img.shields.io/github/last-commit/abaid6790/Ledger?style=flat-square)](https://github.com/abaid6790/Ledger)

</div>

---

## 🧭 Overview

**Ledger** is a complete **Distribution Management System (DMS)** designed around one principle:

> **Every number should come from the same source of truth.**

Instead of maintaining separate stock counts, debtor totals, cash balances, and report calculations, Ledger calculates business state directly from the underlying transactions.

That means:

**Purchase → Stock**

**Sale → Stock + Cash/Debt**

**Return → Stock + Financial adjustment**

**Payment → Cash + Outstanding balance**

**Expense → Cash Book + P&L**

Everything stays connected.

---

## ✨ What Makes Ledger Different?

<table>
<tr>
<td width="50%">

### 📦 Inventory

* Box & pack inventory
* Automatic stock calculation
* Opening stock
* Stock adjustments
* Low-stock detection
* Purchase & sale returns
* Physical-count corrections

</td>

<td width="50%">

### 💰 Financial Management

* Cash Book
* Debtors
* Creditors
* Customer payments
* Supplier payments
* Expenses
* Profit & Loss
* Running cash balance

</td>
</tr>

<tr>
<td>

### 🧾 Transactions

* Purchases
* Sales
* Sale Returns
* Purchase Returns
* Automatic invoice numbering
* Customer/supplier matching
* Printable invoices

</td>

<td>

### 👥 Access Control

* Admin accounts
* Managers
* Salesmen
* Accountants
* Per-module permissions
* Employee-linked users
* Forced first-login password change

</td>
</tr>
</table>

---

# 🏗️ Architecture

```text
                         ┌──────────────────────┐
                         │       Browser        │
                         │   Jinja2 + Tailwind  │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │      Flask App       │
                         │ Application Factory  │
                         └──────────┬───────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          │                         │                         │
          ▼                         ▼                         ▼
   ┌─────────────┐          ┌─────────────┐          ┌─────────────┐
   │ Transactions│          │  Business   │          │    Auth     │
   │ Sales       │          │   Logic     │          │ Permissions │
   │ Purchases   │          │ Stock       │          │ Users       │
   │ Returns     │          │ Balances    │          │ Employees   │
   └──────┬──────┘          │ Payments    │          └─────────────┘
          │                 └──────┬──────┘
          │                        │
          └────────────────┬───────┘
                           ▼
                  ┌──────────────────┐
                  │   SQLAlchemy     │
                  │       ORM        │
                  └────────┬─────────┘
                           ▼
                  ┌──────────────────┐
                  │   PostgreSQL     │
                  │ Single Source    │
                  │    of Truth      │
                  └──────────────────┘
```

---

# 🚀 Core Features

## 📦 Product & Inventory Management

Products support both **boxes and individual packs**.

Each product can have:

* Unique SKU
* Packs per box
* Box price
* Automatically calculated pack price
* Minimum stock level
* Historical purchase pricing
* Current stock
* Potential sales value

### Stock Formula

```text
Current Stock
=
Opening Stock
+ Purchases
+ Sale Returns
- Sales
- Purchase Returns
± Stock Adjustments
```

The stock engine lives in one place:

```text
app/stock.py
```

Every module reads from the same calculation.

---

## 🛒 Purchases

Purchases support:

* Supplier auto-creation
* Supplier matching
* Existing/new products
* Box or pack quantities
* Historical purchase prices
* Automatic stock updates
* Credit purchases
* Cash purchases
* Purchase returns

When an existing product is purchased again, its default price can be updated for future transactions while the historical purchase retains its original price.

---

## 💵 Sales

Sales include:

* Customer auto-creation
* Box/pack selling
* Live stock validation
* Cash sales
* Credit sales
* Partial payments
* Required **Booked By** employee
* Automatic invoice numbers
* Printable invoices

Stock is validated **before the transaction is written**, preventing sales that would push inventory below zero.

---

# 🔄 Returns

Ledger supports both:

### Sale Returns

```text
Original Sale
      ↓
Find Invoice
      ↓
Calculate Remaining Returnable Qty
      ↓
Return Items
      ↓
Stock ↑
Customer Balance ↓
Cash Adjustment
```

### Purchase Returns

```text
Original Purchase
      ↓
Find Invoice
      ↓
Calculate Remaining Returnable Qty
      ↓
Return Items
      ↓
Stock ↓
Supplier Balance ↓
Cash Adjustment
```

Previous returns are automatically considered when calculating remaining returnable quantities.

---

# 👥 Customers & Suppliers

Customers and suppliers are automatically populated from transactions.

Matching uses:

```text
Name
+
Phone
+
Address
```

Each party gets:

* Transaction history
* Aggregated totals
* Outstanding balance
* Payment history
* Invoice history

---

# 💳 Debtors & Creditors

Ledger uses a centralized balance engine:

```text
app/balances.py
```

### Customer balance

```text
Credit Sales
- Sale Returns
- Payments Received
+ Opening Balance
=
Outstanding
```

### Supplier balance

```text
Credit Purchases
- Purchase Returns
- Payments Made
+ Opening Balance
=
Outstanding
```

The same calculation is reused across:

* Dashboard
* Customers
* Suppliers
* Debtors
* Creditors
* Reports

No duplicated balance logic.

---

# 💰 Cash Book

A complete transaction ledger with:

* Running balance
* Date filters
* Transaction-type filters
* Sales
* Purchases
* Payments
* Receipts
* Expenses
* Returns

The running balance accounts for transactions **before the selected filter window**, ensuring filtered views still show the correct balance.

---

# 📊 Reports & Business Intelligence

Ledger includes a unified reporting system.

### Reports

| Report           | Available |
| ---------------- | :-------: |
| Profit & Loss    |     ✅     |
| Sales            |     ✅     |
| Purchases        |     ✅     |
| Sale Returns     |     ✅     |
| Purchase Returns |     ✅     |
| Expenses         |     ✅     |
| Debtors          |     ✅     |
| Creditors        |     ✅     |
| Stock            |     ✅     |

Supported date ranges:

```text
Today
Yesterday
This Month
This Year
Custom Range
```

---

# 📈 Profit & Loss

Profit is calculated using actual transaction history.

```text
Net Sales
    ↓
Sales - Sale Returns
    ↓
- Cost of Goods Sold
    ↓
- Expenses
    ↓
Net Profit
```

COGS uses a **weighted-average purchase cost per pack**, calculated from actual purchase history rather than the product's current selling price.

This prevents changes in the current product price from incorrectly changing historical cost calculations.

---

# 🚚 Daily Load Card

The Load Card is generated directly from the day's sales.

```text
Sales Data
    ↓
Customer
    ↓
Product
    ↓
Quantity
    ↓
Total
```

No duplicate manual entry.

Supports filtering by:

* Date
* Salesman
* Customer
* Product

And includes a printable view.

---

# 🧾 Invoice System

A centralized invoice system provides a searchable view of:

* Sales
* Purchases
* Sale Returns
* Purchase Returns
* Customer Receipts
* Supplier Receipts

Every document has a printable version.

Printing settings support:

* A4
* Thermal printer width
* Margins
* Business logo
* Business information
* Customer information

---

# 🔐 Role-Based Permissions

Phase 9 adds a flexible permission system.

Instead of relying only on roles, access can be controlled **per user and per module**.

### Available roles

```text
ADMIN
MANAGER
SALESMAN
ACCOUNTANT
```

Admins can customize individual permissions after selecting a role.

Example:

```text
Salesman

☑ Sales
☑ Customers
☐ Purchases
☐ Suppliers
☐ Reports
☐ Backup
☐ Settings
☐ Users
```

### Permission enforcement

Permissions are enforced centrally through a request-level check.

```text
Request
   ↓
Authentication
   ↓
Permission Check
   ↓
Allowed ───────► Route
   │
   └────────────► 403
```

The sidebar also hides modules the user cannot access.

---

# 🔑 Secure User Management

Admin-controlled user creation means:

* No public registration
* Employee-linked accounts
* Auto-generated passwords
* Password shown only once
* Passwords never stored in plaintext
* Forced password change on first login
* Admin password reset
* Self-service password changes
* Last-admin protection

### First Login

```text
Admin creates account
        ↓
System generates password
        ↓
Password shown once
        ↓
User logs in
        ↓
Forced password change
        ↓
Normal system access
```

---

# 🛡️ Data Safety

Ledger includes multiple safeguards around business data.

### Stock Protection

A stock decrease is rejected if:

```text
Requested Reduction > Available Stock
```

### Transaction Protection

Transactions with existing returns cannot be edited/deleted when doing so would invalidate those returns.

### Purchase Protection

Deleting or reducing a purchase re-validates subsequent stock usage.

### Invoice Protection

Invoice numbers are generated atomically and are never reused after deletion.

---

# 💾 Backup & Restore

Ledger provides a complete business backup system.

A backup contains the business data across the system, including:

```text
Products
Customers
Suppliers
Employees
Sales
Purchases
Returns
Transactions
Expenses
Opening Balances
Settings
Audit Logs
...
```

### Restore

```text
Backup JSON
     ↓
RESTORE confirmation
     ↓
Dependency-safe wipe
     ↓
Restore inside transaction
     ↓
Success
```

If anything fails:

```text
ROLLBACK
```

Nothing is left partially restored.

---

# ☢️ Danger Zone

The reset system completely clears business transaction data.

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

User logins and settings remain intact.

Reset requires confirmation using the exact configured business name.

---

# 🧮 Verified Business Example

The stock engine was verified using the project's worked example:

```text
Purchase:
10 boxes

Packs per box:
20

Total:
200 packs

Sale:
2 boxes = 40 packs
5 packs = 5 packs

Remaining:
200 - 45

= 155 packs
```

### Result

```text
155 packs
```

The result is reproduced through the Flask/PostgreSQL implementation using the centralized stock engine.

---

# 🧪 Migration & Reliability

The system has been tested beyond fresh-install scenarios.

One example was the Phase 9 migration.

New fields were added to existing tables:

```text
users.permissions
users.must_change_password
employees.email
```

The migration was tested against a simulated existing database to ensure existing records could safely migrate instead of failing because of new non-null fields.

---

# 🗂️ Project Structure

```text
Ledger/
│
├── app/
│   ├── __init__.py
│   ├── extensions.py
│   ├── models.py
│   │
│   ├── stock.py
│   ├── balances.py
│   ├── payments.py
│   ├── parties.py
│   ├── invoice_numbers.py
│   ├── returns_helpers.py
│   ├── dashboard_queries.py
│   ├── reports_queries.py
│   ├── date_ranges.py
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
├── static/
│   └── css/
│
├── migrations/
├── seed.py
├── config.py
├── wsgi.py
├── requirements.txt
├── .env.example
└── README.md
```

---

# 🛠️ Technology Stack

<div align="center">

| Technology                     | Purpose                       |
| ------------------------------ | ----------------------------- |
| 🐍 **Python**                  | Core application language     |
| 🌶️ **Flask 3**                | Web framework                 |
| 🐘 **PostgreSQL**              | Relational database           |
| 🧱 **SQLAlchemy**              | ORM                           |
| 🔄 **Alembic / Flask-Migrate** | Database migrations           |
| 🔐 **Flask-Login**             | Authentication                |
| 🔑 **Werkzeug**                | Password hashing              |
| 🎨 **Jinja2**                  | Server-side rendering         |
| 💨 **Tailwind CSS**            | UI styling                    |
| ⚡ **Vanilla JavaScript**       | Small interactive UI features |
| 🚀 **Gunicorn**                | Production WSGI server        |

</div>

---

# 🎨 Design System

Ledger uses a restrained business-focused visual system.

```text
INK      #14202E
PAPER    #F6F4EF
AMBER    #C9822E
FOREST   #2F6B4F
RUST     #AE4A3C
```

### Typography

```text
Display → Space Grotesk
UI      → IBM Plex Sans
Numbers → IBM Plex Mono
```

The interface uses server-rendered Jinja2 templates with Tailwind styling and small amounts of vanilla JavaScript.

No React.

No Next.js.

No JavaScript framework.

No frontend build dependency.

---

# ⚙️ Getting Started

## 1. Clone

```bash
git clone https://github.com/abaid6790/Ledger.git
cd Ledger
```

## 2. Create Virtual Environment

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

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## 4. Configure Environment

```bash
copy .env.example .env
```

or on Linux/macOS:

```bash
cp .env.example .env
```

Configure:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/ledger
SECRET_KEY=your-long-random-secret
```

## 5. Run Database Migrations

```bash
flask db upgrade
```

## 6. Seed Initial Admin

```bash
python seed.py
```

## 7. Start the Application

```bash
flask run
```

Open:

```text
http://localhost:5000
```

---

# 🔑 Default Development Login

```text
Username: admin
Password: admin123
```

> ⚠️ Change the password immediately when using the application outside local development.

There is intentionally **no public registration page**.

Additional accounts are created by an administrator through the Users module.

---

# 🚀 Production

For a production deployment:

```bash
gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app
```

Set:

```env
FLASK_DEBUG=0
```

The Tailwind CDN should also be replaced with a compiled production build before deployment.

---

# 🗺️ Development Roadmap

```text
Phase 1  Foundation              ████████████████████ ✅
Phase 2  Master Data             ████████████████████ ✅
Phase 3  Core Transactions       ████████████████████ ✅
Phase 4  Returns                 ████████████████████ ✅
Phase 5  Money & Accounts        ████████████████████ ✅
Phase 6  Intelligence & Reports  ████████████████████ ✅
Phase 7  Operations              ████████████████████ ✅
Phase 8  Backup & Administration ████████████████████ ✅
Phase 9  Permissions Add-on      ████████████████████ ✅
```

### Current Status

> **Core system complete — 9 phases implemented and verified.**

---

# ⚠️ Known Simplifications

The current implementation intentionally keeps several areas simple.

<details>
<summary><b>Click to expand</b></summary>

### Backup History

Restoring a backup clears the in-app backup history because the history table is connected to user records.

The actual JSON backup files remain on disk.

### Danger Zone

Reset clears business data but keeps:

* User accounts
* Settings

This prevents the administrator from accidentally locking themselves out.

### Purchase Editing

Existing purchase lines can have quantities, prices and discounts adjusted, but new lines cannot be added during editing.

### Audit Trail

Audit records are fully stored with before/after snapshots where applicable, but there is currently no dedicated UI viewer.

### Costing

COGS currently uses full-history weighted-average purchase cost.

A future FIFO or moving-average implementation could provide more granular inventory costing.

### Debtor/Creditor Allocation

Balances are currently calculated at aggregate level rather than allocating payments and returns to individual invoices.

### Returns

Returns currently use the original per-pack price and do not have independent discount/tax fields.

### Credit Expenses

Credit expenses are recorded but are not currently represented as general outstanding accounts payable.

</details>

---

# 🔒 Security Note

During development, an unauthorized version of the project was discovered containing a public registration system where the first registered user could become an administrator.

That functionality was **not part of the intended system** and was removed.

The intended authentication model is:

```text
Administrator
      ↓
Creates Employee/User
      ↓
Assigns Role + Permissions
      ↓
System Generates One-Time Password
      ↓
User First Login
      ↓
Mandatory Password Change
```

There is no public self-registration flow in the intended implementation.

---

# 📸 Screenshots

> Add your actual application screenshots to the `screenshots/` folder and uncomment the images below.

```text
screenshots/
├── dashboard.png
├── sales.png
├── purchases.png
├── stock.png
├── reports.png
├── cash-book.png
├── customers.png
├── suppliers.png
├── users.png
└── invoices.png
```

Example:

<div align="center">

<img src="screenshots/dashboard.png" width="90%"/>

<br><br>

<img src="screenshots/sales.png" width="90%"/>

</div>

---

# 🧠 Core Engineering Principles

### 01 — Single Source of Truth

Business figures are calculated from transactional data instead of duplicated cached values.

### 02 — Database First

PostgreSQL is the authoritative source for business state.

### 03 — Transaction Safety

Critical operations use database transactions and rollback on failure.

### 04 — Centralized Business Logic

Important calculations live in dedicated modules:

```text
stock.py
balances.py
payments.py
invoice_numbers.py
returns_helpers.py
```

### 05 — Server-Side Simplicity

The application deliberately avoids unnecessary frontend complexity.

```text
Flask
+
Jinja2
+
Tailwind
+
Vanilla JS
```

---

# 📚 Engineering Highlights

Some of the most important implementation details include:

* Atomic invoice-number generation using row locking
* Centralized stock calculation
* Centralized debtor/creditor calculation
* Dependency-safe backup restoration
* Transactional restore with rollback
* Stock validation before writes
* Return-aware transaction protection
* Last-admin protection
* Centralized permission enforcement
* Historical purchase-cost snapshots
* Employee-linked authentication
* Automatic customer/supplier matching
* Running cash-book balance
* Opening balances integrated directly into calculations
* Audit logging for business mutations

---

# 🧩 Why Flask?

Ledger was intentionally rebuilt from an earlier React/Next.js implementation using:

```text
Python
Flask
PostgreSQL
Jinja2
```

The goal was to create a simpler server-rendered architecture without:

```text
Node.js
React
Next.js
Frontend build pipeline
```

Small amounts of vanilla JavaScript remain only where dynamic invoice interactions require them.

---

# 📌 Project Status

<div align="center">

### 🟢 ACTIVE DEVELOPMENT

**Core DMS functionality:** Complete
**Database architecture:** PostgreSQL
**Authentication:** Complete
**Permissions:** Complete
**Reports:** Complete
**Backup/Restore:** Complete
**Audit Trail:** Implemented
**Production hardening:** Ongoing

</div>

---

# 🤝 Contributing

Contributions, bug reports and improvements are welcome.

Before submitting a pull request:

1. Create a branch
2. Make the change
3. Test the affected business logic
4. Verify database migrations
5. Check permission boundaries
6. Submit a pull request with a clear description

See `CONTRIBUTING.md` for project-specific guidelines.

---

# 📄 License
Abaid-ur-Rehman
AL Engineer | ML Engineer | Python Developer
---


# ✍ Author

This project is licensed under the **MIT License**.

See [`LICENSE`](LICENSE) for details.

---

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:2F6B4F,50:C9822E,100:14202E&height=120&section=footer" width="100%"/>

### Built with Python 🐍 · Flask 🌶️ · PostgreSQL 🐘

**Ledger — One source of truth for your distribution business.**

<br>

<img src="https://komarev.com/ghpvc/?username=abaid6790&label=Repository%20Views&color=C9822E&style=flat-square" alt="Repository Views"/>

</div>
