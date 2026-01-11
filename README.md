# 🏮 Haveli Electricals: Inventory & Billing Hub

A professional-grade, dark-themed Point of Sale (POS) and Inventory Management system tailored for retail electrical shops. Built with **Streamlit**, **Supabase**, and **ReportLab**.

---

## ✨ Key Features

* **⚡ High-Speed Billing:** Add items to a virtual cart, adjust quantities/prices on the fly, and finalize sales with a single click.
* **📄 Professional PDF Invoices:** Generates A5-sized digital receipts with automatic date stamping, payment mode details, and clean itemized lists.
* **💬 WhatsApp Integration:** Send "magic links" to customers to share their invoices instantly via WhatsApp.
* **🛑 Inventory Integrity:** Automated stock deduction upon sale and stock restoration if a transaction is voided.
* **⚙️ Dynamic Configuration:** Manage shop name, address, contact details, and UPI ID directly from the UI to update all invoices instantly.
* **🔴 Sophisticated UI:** A deep-red and charcoal aesthetic designed for eye comfort and professional retail environments.

---

## 🚀 Deployment Guide (Streamlit Cloud)

### 1. Preparation
Ensure your repository contains:
* `app.py` (Main entry point)
* `src/` (Database and Utility logic)
* `requirements.txt` (List of dependencies)
* `.gitignore` (To exclude sensitive files like `.env`)

### 2. GitHub Push
```bash
git init
git add .
git commit -m "Final professional release"
git remote add origin [https://github.com/YOUR_USERNAME/haveli-inventory.git](https://github.com/YOUR_USERNAME/haveli-inventory.git)
git branch -M main
git push -u origin main