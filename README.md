# 🌾 Khedut & Vepari Hisab ERP (Agri-Mandi Billing & Accounting System)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.1%2B-092E20.svg)](https://www.djangoproject.com/)
[![Database](https://img.shields.io/badge/Database-SQLite-003B57.svg)](https://www.sqlite.org/)
[![Responsive](https://img.shields.io/badge/Design-Fully%20Responsive-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-Proprietary-orange.svg)]()

A comprehensive, enterprise-grade **Django Web Application ERP** custom-built for Agricultural Marketing Yards (APMC Mandi), Tobacco Sub-Markets, and Agri-commodity trading commissions.

This system seamlessly unifies **Farmer Purchases**, **Trader Sales**, **Official GST Tax Invoicing**, **Customer/Vendor Ledgers (Khata Vahi)**, **Daily Cashbook (Rozmel)**, and **Operational Expense Management** on top of a reliable SQLite persistence database.

---

## 🌟 Key Features & Modules

### 1. 🌾 Farmer Purchase Billing (Khedut Kharedi Bill)
- Supports both standard (kacha) estimates and formal GST purchase bills.
- Standard agricultural weight-to-rate computation formula:
  $$\text{Amount} = \frac{\text{Weight (kg)} \times \text{Rate per Maund (20 kg)}}{20}$$
- Automated line calculations for packing sacks/bags (Bardan @ ₹15/bag), labor (Majuri), deductions (Kapat), and applicable GST.
- Instant tracking of paid vs. outstanding dues with clean, print-ready voucher receipts (`@media print`).

### 2. 🏪 Trader Sales Invoicing (Vepari Vechan Bill)
- **Automatic Matching Mode:** Intelligently picks unbilled farmer purchase lots for selected buyers.
- **Manual Entry Mode:** Direct commodity item entry with custom weight, rates, and sacks.
- Built-in automatic calculation of **1.5% commission**, statutory Mandi market cess, sack costs, handling charges, transport freight, and taxes.
- Customized commercial bill layout for mandi traders.

### 3. 🧾 Official GST Tax Invoices
- Complete GST-compliant invoice templates featuring Buyer Name, Address, and GSTIN.
- Automatic tax breakdown: Intrastate (CGST + SGST) and Interstate (IGST).
- Pre-configured bank account details (IFSC, Account Number, Branch) and authorized signatory sections.

### 4. 📖 Ledger & Account Reconciliation (Khata Vahi)
- Date-range and party-specific account filtering for both farmers and traders.
- Streamlined payment capture: Farmer payout vouchers and Trader receipt vouchers (Cash / Bank).
- Live balance tracking showing receivables (Lehnu) and payables (Denu).

### 5. 📅 Daily Cashbook & Balance Sheet (Rozmel)
- Real-time aggregation of daily credit/inflow, debit/outflow, operational overheads, and net liquid balance.
- Live tracking of **Cash in Hand (Tijori Cash)** and **Bank Balance**.

### 6. 💸 Expense Tracking (Kharch Nondh)
- Categorized overhead entry for tea/refreshments, office stationery, rent, electricity, freight, and vehicle fuel.

### 7. ⚙️ Firm Master Settings & Trader Directory
- Centralized configuration for Firm Name, GSTIN, Bank Details, and Signatory name.
- Custom rate configurations: Bardan rate, Market cess rate, and Commission percentage.
- Trader Master directory for quick auto-complete dropdowns during bill generation.

### 8. 📱 Responsive Architecture & Theme Engine
- **Mobile First & Off-Canvas Navigation:** Seamless drawer navigation for smartphones and tablets.
- **Light & Dark Mode:** Built-in royal navy and electric cyan theme toggle with persistent user preferences.
- **Dedicated Keyboard Shortcuts (F2–F9):** Fast switching between billing modules for power users.

---

## 🛠️ Technology Stack

- **Backend:** Python 3.10+, Django 5.1
- **Database:** SQLite3 (`db.sqlite3` with pre-configured schemas and migrations)
- **Frontend:** Semantic HTML5, Vanilla Modern CSS3 (CSS Grid & Flexbox), Vanilla JavaScript (No heavy runtime libraries)
- **Design Tokens:** Royal Deep Midnight Navy & Electric Cyan Fintech Palette
- **Printing Engine:** Pure CSS `@media print` engine formatted for A4 & thermal voucher receipts

---

## 🚀 Quick Setup & Installation Guide

### Prerequisites
1. **Python 3.10 or higher** installed on your computer.
   - Download from [python.org](https://www.python.org/downloads/).
   - ⚠️ **Important:** During Windows installation, check the box: **`Add python.exe to PATH`**.

---

### Option 1: 1-Click Automatic Launch (Windows)

1. Extract or clone this repository to your target folder.
2. Double-click the **`run_app.bat`** file in the root directory.
3. The script will automatically:
   - Check and verify your Python & Django environment.
   - Install missing dependencies from `requirements.txt`.
   - Apply any pending database migrations.
   - Launch your default browser at **`http://127.0.0.1:8000/`**.

---

### Option 2: Manual Setup via Terminal / Command Prompt

#### Step 1: Open Terminal in Project Directory
Open Command Prompt / PowerShell in the project directory:
```bash
cd c:\path\to\khedut-vepari-hisab-erp
```

#### Step 2: Create and Activate Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate on Windows:
venv\Scripts\activate

# Activate on Linux / macOS:
source venv/bin/activate
```

#### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```
*(Or directly: `pip install django`)*

#### Step 4: Apply Database Migrations
```bash
python manage.py migrate
```

#### Step 5: (Optional) Seed Sample Master Data
```bash
python manage.py seed_data
```

#### Step 6: Start the Development Server
```bash
python manage.py runserver 127.0.0.1:8000
```

#### Step 7: Open in Your Browser
- 🌐 **ERP Main Application:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- ⚙️ **Django Admin Portal:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
  - **Default Username:** `admin`
  - **Default Password:** `admin`

---

## 📶 Access over Local Network / Office Wi-Fi

If your office has multiple PCs or you want to use tablets/phones on the same Wi-Fi router:

1. Launch the server binding to all network interfaces:
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```
2. Find the host computer's local IP address (run `ipconfig` in Command Prompt, e.g. `192.168.1.15`).
3. On any mobile phone, tablet, or laptop connected to the same Wi-Fi, open the browser and navigate to:
   ```text
   http://192.168.1.15:8000/
   ```
   All connected devices will share the same live database instantly!

---

## ⌨️ Fast Keyboard Shortcuts

| Shortcut Key | Module Destination |
| :---: | :--- |
| **`F2`** | 🌾 Farmer Purchase Bill |
| **`F3`** | 🏪 Trader Sales Bill |
| **`F4`** | 🧾 GST Tax Invoice |
| **`F6`** | 📖 Khata Vahi (Ledger) |
| **`F7`** | 📅 Daily Cashbook (Rozmel) |
| **`F8`** | 💸 Expense Book |
| **`F9`** | ⚙️ Master Firm Settings |

---

## 📁 Project Directory Structure

```text
khedut-vepari-hisab-erp/
├── billing/                       # Core ERP Billing application
│   ├── management/commands/       # Custom management commands (seed_data)
│   ├── migrations/                # Database migrations
│   ├── admin.py                   # Django admin registrations
│   ├── models.py                  # Database schemas (Farmer, Trader, Bills, Ledgers)
│   ├── urls.py                    # URL route definitions
│   └── views.py                   # Business logic and transaction processors
├── hisab_core/                    # Django project core configuration
│   ├── asgi.py                    # ASGI server entrypoint
│   ├── settings.py                # Global settings and installed apps
│   ├── urls.py                    # Root URL router
│   └── wsgi.py                    # WSGI server entrypoint
├── static/                        # Static assets
│   ├── css/style.css              # Custom SaaS design system with Dark/Light theme
│   └── js/app.js                  # Frontend interactivity & real-time calculators
├── templates/billing/             # HTML5 templates
│   ├── index.html                 # Main single-page interactive ERP dashboard
│   ├── login.html                 # Authentication login screen
│   ├── register.html              # User registration screen
│   ├── print_farmer_bill.html     # Farmer purchase voucher print template
│   ├── print_trader_bill.html     # Trader invoice print template
│   └── print_gst_bill.html        # Official GST invoice print template
├── db.sqlite3                     # SQLite database file
├── manage.py                      # Django management script
├── requirements.txt               # Python package dependencies
├── run_app.bat                    # Windows 1-click startup automation script
├── .gitignore                     # Git ignore rules
└── README.md                      # Project documentation
```

---

## ❓ Frequently Asked Questions (FAQ)

**Q: `'python' is not recognized as an internal or external command`?**  
**A:** Python is either not installed or not added to your system PATH. Re-run the Python installer and ensure the **`Add python.exe to PATH`** checkbox is selected.

**Q: `Error: That port is already in use`?**  
**A:** Another service is using port 8000. Launch with an alternative port:
```bash
python manage.py runserver 127.0.0.1:8080
```
Then visit `http://127.0.0.1:8080/`.

**Q: How do I create a new administrator account?**  
**A:** Run the following command in your terminal and follow the prompts:
```bash
python manage.py createsuperuser
```

---

## 📄 License & Ownership
Copyright © 2026. All rights reserved. Designed and developed for APMC Mandi, Tobacco Trade, and Agri-Commodity Accounting.
