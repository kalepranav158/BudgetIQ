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

```bash
pytest
```

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
