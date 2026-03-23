# Smart Budget ML System

Smart Budget ML System is a transition of the original Smart Budget Management System from a single Django upload flow into a modular, ML-ready architecture.

Current phase: transaction parsing, normalization, storage, analytics, and rule-based categorization. ML artifacts are present but disabled by default.

## What It Does

- Parses password-protected YONO SBI or SBI-style PDF statements
- Extracts transaction date, description, debit, credit, balance, and counterparty fields
- Categorizes transactions with a rule-based engine and saved counterparty mappings
- Stores normalized transactions for analytics and future ML activation
- Exposes FastAPI endpoints for transactions, category summary, and monthly analytics
- Keeps the existing Django upload UI available as a compatibility layer

## Tech Stack

- Python
- Django for the legacy upload interface
- FastAPI for the normalized API layer
- SQLAlchemy with SQLite by default for normalized storage
- pdfplumber for PDF extraction


## Project Layout

```text
backend/
database/
docs/
ml/
smartbudget/
tests/
main.py
requirements.txt
```

## Run Locally

1. Create and activate a virtual environment.
2. Install dependencies.

```bash
pip install -r requirements.txt
```

3. Import a statement into the normalized store.

```bash
python main.py path/to/statement.pdf --password YOUR_PASSWORD
```

4. Start the API.

```bash
uvicorn backend.api.main:app --reload
```

5. Optional: run the legacy Django UI.

```bash
cd smartbudget
python manage.py migrate
python manage.py runserver
```

## ML Status

- ML files are scaffolded under `ml/` and can be enabled later.
- Runtime categorization is currently rule-based.
- To enable ML fallback later, set `ENABLE_ML_CATEGORIZATION=1` in `.env` after preparing model artifacts.

## Running Tests
=======
# BudgetIQ
A full-stack personal finance platform that automates transaction ingestion, categorization, and analytics using a hybrid architecture of **FastAPI (backend)** and **Django (frontend/admin dashboard)**.

---

## 🚀 Overview

This project is designed to solve real-world financial tracking problems by extracting transaction data from bank PDFs, categorizing expenses intelligently, and presenting insights through an interactive dashboard.

It follows a **modern, scalable architecture**:

* ⚙️ FastAPI → Core backend (processing + APIs)
* 🌐 Django → UI + admin dashboard
* 🗄️ SQLite → Normalized transaction storage
* 🤖 ML-ready → Future intelligent categorization

---

## 🧠 Key Features

### 📥 Data Ingestion

* Upload bank statements (PDF)
* Extract:

  * Date
  * Description
  * Debit/Credit
  * Balance
  * UPI / Counterparty

---

### 🧾 Smart Categorization

* Rule-based classification
* Custom category mappings
* Income auto-detection
* ML integration (planned)

---

### 📊 Analytics Dashboard

* Monthly spending summary
* Category-wise expense breakdown
* Income vs expense tracking
* Trend analysis (future scope)

---

### 🔄 Deduplication System

* Prevents duplicate transaction entries
* (Improvement planned: content-based hashing)

---

## 🏗️ Architecture

```text
User → Django UI → FastAPI API → Services → Database → Analytics → UI
```

### 🔹 Backend (FastAPI)

* Transaction parsing
* Categorization engine
* Analytics computation
* REST API endpoints

### 🔹 Frontend (Django)

* File upload interface
* Dashboard visualization
* Admin controls

---

## 📁 Project Structure

```text
backend/        → FastAPI services (core logic)
database/       → DB connection & schema
ml/             → ML models (future scope)
smartbudget/    → Django frontend
docs/           → Project documentation
tests/          → Unit tests
main.py         → CLI ingestion tool
```

---

## 🗄️ Database

* SQLite (normalized schema)
* Tables:

  * transactions
  * category_mappings

---

## ⚠️ Current Status

* ✅ FastAPI backend functional
* ✅ PDF parsing & categorization working
* ✅ Analytics service implemented
* ⚠️ Django integration in progress
* ⚠️ ML categorization not yet enabled
* ⚠️ Deduplication improvement needed

---

## 🧪 Testing
>>>>>>> 80ff76ab61e8edc9fffb69419c00785266f338c8

```bash
pytest
```

<<<<<<< HEAD
## Notes

- The canonical API and data path is the normalized database in `database/connection/`.
- The Django app remains available during migration and still stores its own legacy tables.
- `.env.example` documents the environment variables used by both paths.
=======
*(Note: requires proper module path configuration)*

---

## 🔧 Setup Instructions

### 1. Clone Repository

```bash
git clone https://github.com/your-username/smart-budget-management-system.git
cd smart-budget-management-system
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run FastAPI Backend

```bash
uvicorn backend.api.main:app --reload
```

### 5. Run Django Server

```bash
cd smartbudget
python manage.py runserver
```

---

## 📌 Future Enhancements

* 🤖 ML-based transaction categorization
* 📈 Advanced analytics (forecasting, anomaly detection)
* ☁️ PostgreSQL integration
* 🔐 User authentication system
* 📱 Mobile-friendly UI

---

## 💼 Resume Highlight

> Designed and developed a hybrid financial analytics platform using FastAPI and Django, enabling automated transaction processing, intelligent categorization, and real-time expense insights.

---

## 📄 License

This project is open-source and available under the MIT License.
>>>>>>> 80ff76ab61e8edc9fffb69419c00785266f338c8
