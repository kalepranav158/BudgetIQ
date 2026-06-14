# BudgetIQ Development Guide

## 🛠️ Development Environment Setup

### Prerequisites
- Python 3.13+
- Node.js 18+
- Git
- pip, virtualenv
- PostgreSQL (optional, for production)

### Windows Setup

```bash
# Clone repository
git clone https://github.com/kalepranav158/BudgetIQ.git
cd BudgetIQ

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Frontend setup
cd frontend
npm install
cd ..

# Database setup
python manage.py migrate
python manage.py createcachetable

# Create superuser (optional)
python manage.py createsuperuser
```

### Linux/Mac Setup

```bash
# Clone repository
git clone https://github.com/kalepranav158/BudgetIQ.git
cd BudgetIQ

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Frontend setup
cd frontend
npm install
cd ..

# Database setup
python manage.py migrate
python manage.py createcachetable
```

---

## 🚀 Running Services

### Development Server (All Services)

**Terminal 1: Django API Server**
```bash
.venv\Scripts\activate  # Windows: activate venv
# source .venv/bin/activate  # Linux/Mac

python manage.py runserver
# Django runs on: http://localhost:8000
```

**Terminal 2: FastAPI Service**
```bash
.venv\Scripts\activate

cd backend/fastapi_service
uvicorn main:app --reload --port 8001
# FastAPI runs on: http://localhost:8001
# Docs available at: http://localhost:8001/docs
```

**Terminal 3: Frontend Dev Server**
```bash
cd frontend
npm run dev
# Frontend runs on: http://localhost:5173
```

### Accessing Services
- Frontend: http://localhost:5173
- Django Admin: http://localhost:8000/admin
- Django API: http://localhost:8000/api
- FastAPI Docs: http://localhost:8001/docs
- FastAPI ReDoc: http://localhost:8001/redoc

---

## 🧪 Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test File
```bash
pytest tests/test_hurdle_model.py -v
pytest tests/test_active_learning.py -v
```

### Run with Coverage
```bash
pytest --cov=ml --cov=backend tests/
```

### Run Only Active Learning Tests
```bash
pytest tests/test_active_learning.py -v -s
```

### Run Only Hurdle Model Tests
```bash
pytest tests/test_hurdle_model.py -v -s
```

### Frontend Tests
```bash
cd frontend
npm run test
```

---

## 🧠 ML Development

### Training Models

#### Train Two-Stage Hurdle Model
```bash
# Full hurdle model training
python ml/training/train_hurdle.py

# Output:
# - ml/models/hurdle_stage1_classifier.joblib
# - ml/models/hurdle_stage2_quantile_regressor.joblib
# - Manifests with metadata and metrics
```

#### Train Category Classifier
```bash
python ml/training/train_classifier.py

# Output:
# - ml/models/category_classifier.joblib
# - Metrics report
```

#### Train Regression Model
```bash
python ml/training/train_regressor.py

# Output:
# - ml/models/daily_spend_regressor.joblib
# - Performance metrics
```

### Model Inference

#### Generate Spending Forecasts
```python
from ml.inference.hurdle_forecast import generate_hurdle_forecast
from datetime import datetime, timedelta

# Generate 7-day forecast
forecast = generate_hurdle_forecast(
    days_ahead=7,
    reference_date=datetime.now()
)

print(forecast)
# Returns:
# {
#     'predictions': [...],
#     'confidence_intervals': [...],
#     'model_version': '...',
# }
```

#### Categorize Transaction
```python
from ml.inference.predict import predict_category

prediction = predict_category(
    description="Amazon Marketplace Purchase",
    amount=450.50
)

print(prediction)
# Returns:
# {
#     'category': 'Shopping',
#     'confidence': 0.94,
#     'alternatives': [...]
# }
```

### Active Learning Workflow

#### Flag Low-Confidence Predictions
```python
from ml.active_learning import flag_low_confidence_transactions

# Flag all predictions with confidence < 0.6
flags_count = flag_low_confidence_transactions(confidence_threshold=0.6)
print(f"Flagged {flags_count} low-confidence predictions")
```

#### Process Corrections
```python
from ml.active_learning import capture_corrections

# Read corrections from CSV
# Format: transaction_id, corrected_category, notes
capture_corrections(csv_path='corrections.csv')
```

#### Trigger Retraining
```python
from ml.active_learning import check_and_trigger_retraining

# Auto-trigger retraining when 80+ corrections accumulated
triggered = check_and_trigger_retraining(threshold=80)
if triggered:
    print("Retraining cycle initiated")
```

#### View Status
```python
from ml.active_learning import get_active_learning_report

report = get_active_learning_report()
print(f"Flagged transactions: {report['flagged_count']}")
print(f"Corrected: {report['corrected_count']}")
print(f"Pending retraining: {report['pending_retraining']}")
```

### Experiment Reporting

```python
from ml.experiment_reporting import ExperimentMetrics

metrics = ExperimentMetrics()

# Generate compliance report
report = metrics.generate_spec_report()

# Print report
import json
print(json.dumps(report, indent=2))

# Validate all 6 specification claims:
# 1. 12,000+ transactions processed
# 2. 98%+ parsing accuracy
# 3. 99% deduplication rate
# 4. 93.4% categorization accuracy
# 5. Rs. 85.4 forecast MAE
# 6. 80%+ manual effort reduction
```

---

## 🗄️ Database Operations

### Migrations

#### Create New Migration
```bash
python manage.py makemigrations
```

#### Apply Migrations
```bash
python manage.py migrate
```

#### View Migration Status
```bash
python manage.py showmigrations
```

#### Rollback Migration
```bash
python manage.py migrate django_app 0010  # Rollback to specific migration
```

### Database Utilities

#### Create Admin User
```bash
python manage.py createsuperuser
```

#### Access Django Shell
```bash
python manage.py shell
```

#### Reset Database
```bash
python manage.py flush  # Warning: Deletes all data!
```

---

## 📝 Code Validation

### Validate All Implementations
```bash
python validate_implementations.py

# Output:
# ✓ Testing hurdle model dataset loading...
# ✓ Testing stratified split...
# ✓ Testing metric computation...
# ✓ Testing trained model loading...
# ✓ Testing active learning DB models...
# ✓ Testing active learning functions...
# ✓ Testing experiment reporting...
# ✓ Testing hurdle model inference...
# ✅ ALL VALIDATIONS PASSED (9 checks)
```

### Code Quality

#### Run Linter
```bash
# Install (if not done)
pip install pylint

# Run linting
pylint ml/ backend/
```

#### Format Code
```bash
# Install (if not done)
pip install black

# Format all Python files
black ml/ backend/ tests/
```

---

## 🔧 Common Development Tasks

### Adding a New API Endpoint

1. **Create Model** (if needed) in `backend/django_app/models.py`:
```python
class MyModel(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
```

2. **Create Serializer** in `backend/django_app/serializers.py`:
```python
from rest_framework import serializers
from .models import MyModel

class MyModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyModel
        fields = ['id', 'name', 'created_at']
```

3. **Create ViewSet** in `backend/django_app/views.py`:
```python
from rest_framework.viewsets import ModelViewSet
from .models import MyModel
from .serializers import MyModelSerializer

class MyModelViewSet(ModelViewSet):
    queryset = MyModel.objects.all()
    serializer_class = MyModelSerializer
```

4. **Register URL** in `backend/django_app/urls.py`:
```python
from rest_framework.routers import DefaultRouter
from .views import MyModelViewSet

router = DefaultRouter()
router.register(r'mymodel', MyModelViewSet)

urlpatterns = router.urls
```

5. **Create Migration**:
```bash
python manage.py makemigrations
python manage.py migrate
```

### Adding a New ML Feature

1. **Feature Engineering** in `ml/features.py`:
```python
def extract_temporal_features(transaction_date):
    """Extract day of week, month, etc."""
    return {
        'day_of_week': transaction_date.weekday(),
        'day_of_month': transaction_date.day,
        'month': transaction_date.month,
    }
```

2. **Update Training** in `ml/training/`:
```python
from ml.features import extract_temporal_features

def train_model(X, y):
    # Apply new features
    features = [extract_temporal_features(d) for d in X]
    # Train model...
```

3. **Test New Feature**:
```bash
pytest tests/ -k feature -v
```

### Adding Tests

1. **Create Test File** `tests/test_new_feature.py`:
```python
import pytest
from ml.features import extract_temporal_features

def test_extract_temporal_features():
    from datetime import datetime
    result = extract_temporal_features(datetime(2026, 6, 14))
    assert result['day_of_week'] == 6  # Sunday
    assert result['month'] == 6
```

2. **Run New Tests**:
```bash
pytest tests/test_new_feature.py -v
```

---

## 🐛 Debugging

### Django Debugging

```python
# In your view or serializer
import pdb; pdb.set_trace()  # Debugger breakpoint
```

### Python Debugging with VSCode

1. Install Python extension
2. Create `.vscode/launch.json`:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Django",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/manage.py",
            "args": ["runserver"],
            "django": true
        }
    ]
}
```

3. Set breakpoints and press F5 to debug

### FastAPI Debugging

Access interactive docs:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

---

## 📊 Development Workflow

### Feature Development Workflow

```bash
# 1. Create feature branch
git checkout -b feature/my-feature

# 2. Make changes
# ... edit files ...

# 3. Run tests
pytest tests/ -v

# 4. Format code
black .

# 5. Validate implementations
python validate_implementations.py

# 6. Commit changes
git add .
git commit -m "feat: add my-feature"

# 7. Push to GitHub
git push origin feature/my-feature

# 8. Create Pull Request on GitHub
```

### Git Workflow

```bash
# View status
git status

# Stage changes
git add <file>
git add .

# Commit
git commit -m "message"

# Push
git push origin <branch>

# Pull latest
git pull origin main

# Create branch
git checkout -b feature/name
```

---

## 📚 Useful Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [scikit-learn Documentation](https://scikit-learn.org/)
- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vitejs.dev/)

---

## ❓ Troubleshooting

### ModuleNotFoundError

**Error**: `ModuleNotFoundError: No module named 'ml'`

**Solution**: Ensure you're running from project root and .venv is activated:
```bash
cd BudgetIQ
.venv\Scripts\activate
python script.py
```

### Database Errors

**Error**: `django.db.utils.OperationalError`

**Solution**: Run migrations:
```bash
python manage.py migrate
```

### Port Already in Use

**Error**: `Address already in use`

**Solution**: Kill process on port:
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
kill -9 <PID>
```

### Import Path Issues

**Error**: `ModuleNotFoundError` when running scripts directly

**Solution**: The ml/training scripts include automatic path resolution:
```python
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))
```

---

**Happy coding! 🚀**
