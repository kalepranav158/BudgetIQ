# BrainIQ Workflows & Operations Guide

This document covers important workflows for managing the BrainIQ transaction classification system.

---

## Table of Contents

1. [Classification System Overview](#classification-system-overview)
2. [Adding Transaction Mappings](#adding-transaction-mappings)
3. [UPI Details Extraction](#upi-details-extraction)
4. [Database Management](#database-management)
5. [API Endpoints Reference](#api-endpoints-reference)
6. [Management Commands](#management-commands)
7. [Troubleshooting](#troubleshooting)

---

## Classification System Overview

The system classifies transactions using a **priority-based matching hierarchy**:

```
1. UPI Account Rules (highest priority)   → upi_id + receiver_name must match exactly
2. Regex Rules                            → pattern matching with customizable priority
3. Keyword Rules                          → simple substring matching
4. ML Predictions (if available)          → fallback ML-based category
5. Default: "other"                       → catch-all category
```

### UPI Details Extraction

When a transaction is parsed, the system extracts:

- **receiver_name**: The UPI counterparty name (e.g., "MAYURESH", "HEMANT P")
- **upi_id**: Bank code + reference ID (e.g., "YESB/Q731754728")

Example transaction:
```
TRANSFER TO 4897694162092 UPI/DR/598732810891/HEMANT P/YESB/Q208692237/Payme
```

Extracted:
```
{
  "name": "HEMANT P",
  "upi_id": "YESB/Q208692237"
}
```

---

## Adding Transaction Mappings

There are **3 types of mappings**. Choose based on your needs:

### Type 1: UPI Account Rules (Best for recurring payments)

**When to use**: Same person pays you regularly via same UPI ID
- Highest priority
- Requires both upi_id AND receiver name to match
- Most accurate for recurring transactions

#### Via Django Shell (Quickest)

```bash
cd "d:\M Projects\BrainIQ"
python manage.py shell
```

```python
from backend.django_app.models import AccountCategoryMapping

# Add a UPI mapping
AccountCategoryMapping.objects.create(
    upi_id="UTIB/GPAYRECHAR",      # Extract from transaction description (e.g., "UTIB/GPAYRECHAR")
    name="GOOGLE I",                # Receiver name (will be uppercased)
    category="recharge",            # [lunch, tea, extra, cash_withdrawal, recharge, credit, other]
    priority=1                      # Lower number = higher priority
)

# View all UPI mappings
print(list(AccountCategoryMapping.objects.all().values()))

# Example: View all mappings by category
for mapping in AccountCategoryMapping.objects.filter(category="recharge"):
    print(f"{mapping.upi_id} + {mapping.name} → {mapping.category}")
```

#### Via API Endpoint

```bash
curl -X POST http://localhost:8000/create_account_mapping \
  -d "upi_id=YESB/Q731754728&name=HEMANT&category=tea&priority=1"
```

#### Via mapping.py (for defaults)

Edit [mapping.py](../mapping.py) to customize defaults. The script uses `get_or_create()` to avoid duplicates on re-run:

```python
def seed_default_mappings() -> None:
    # Keyword mapping (simplest)
    CategoryMapping.objects.get_or_create(
        keyword="ZOMATO", 
        defaults={"category": "lunch"}
    )

    # Regex patterns (flexible)
    RegexCategoryMapping.objects.get_or_create(
        name="UPI_MAYURESH",
        defaults={"pattern": "MAYURESH", "category": "lunch", "priority": 2}
    )

    # UPI account mappings (highest priority)
    AccountCategoryMapping.objects.get_or_create(
        upi_id="YESB/Q208692237",
        name="MAYURESH",
        defaults={"category": "lunch", "priority": 1}
    )

    AccountCategoryMapping.objects.get_or_create(
        upi_id="YESB/Q731754728",
        name="HEMANT",
        defaults={"category": "tea", "priority": 1}
    )

    AccountCategoryMapping.objects.get_or_create(
        upi_id="UTIB/GPAYRECHAR",
        name="GOOGLE I",
        defaults={"category": "recharge", "priority": 1}
    )
```

Then run:
```bash
python manage.py seed_mappings
```

---

### Type 2: Regex Rules (For merchants, patterns)

**When to use**: Multiple people/accounts with same merchant name
- Medium priority
- Flexible pattern matching (case-insensitive)
- Supports complex patterns: `SWIGGY|ZOMATO|BUNDLE`

#### Via Django Shell

```bash
python manage.py shell
```

```python
from backend.django_app.models import RegexCategoryMapping

# Add a regex mapping
RegexCategoryMapping.objects.create(
    name="UPI_MAYURESH",
    pattern="MAYURESH",             # Regex pattern (e.g., "SWIGGY|ZOMATO")
    category="lunch",
    priority=2                      # Higher priority = checked earlier
)

# View all regex mappings
print(list(RegexCategoryMapping.objects.all().values()))
```

#### Via API Endpoint

```bash
curl -X POST http://localhost:8000/create_regex_mapping \
  -d "name=UPI_MAYURESH&pattern=MAYURESH&category=lunch&priority=2"
```

#### Common Patterns

```python
# Regex patterns examples
"ZOMATO|SWIGGY|BUNDL"              # Food delivery apps
"NYKAA|MYNTRA"                     # Shopping
"NETFLIX|HOTSTAR|PRIME"            # Subscriptions
"ATM|CASH\s+WITHDRAWAL"            # ATM withdrawals
"SALARY|SALARY CREDIT"             # Salary
"GOOGLE|GPAYRECHAR"                # Google Pay recharge
"AIRTEL|JIOTOP|VODAFONE|IDEA|BSNL" # Mobile recharges
```

---

## Recharge Category Workflow

The system now categorizes mobile/telecom recharges automatically. 

### Supported Recharge Providers

Currently seeded:
```
Google Pay Recharges  → UTIB/GPAYRECHAR + GOOGLE I
Airtel, Jio, Vodafone, Idea, BSNL (regex) → AIRTEL|JIOTOP|VODAFONE|IDEA|BSNL
```

### Example Recharge Transaction

```
TRANSFER TO 4897691162095 UPI/DR/510436257862/Google I/UTIB/gpayrechar/UPI
Amount: 19
```

**Extracted**:
```
{
  "name": "GOOGLE I",
  "upi_id": "UTIB/GPAYRECHAR"
}
```

**Result**: Automatically categorized as **recharge** (priority 1 - UPI account rule match)

### Adding New Telecom Providers

For a new recharge provider, add via Django shell:

```bash
python manage.py shell
```

```python
from backend.django_app.models import AccountCategoryMapping, RegexCategoryMapping

# Specific UPI (highest accuracy)
AccountCategoryMapping.objects.create(
    upi_id="ICIC/AIRTELMORE",    # Extract from actual transaction
    name="AIRTEL RECHARGE",
    category="recharge",
    priority=1
)

# Or via regex (fallback)
RegexCategoryMapping.objects.create(
    name="MY_TELECOM",
    pattern="AIRTEL|AIRTELMORE|AIRTEL DATA",
    category="recharge",
    priority=2
)
```

---

**When to use**: Quick catch-all patterns
- Lowest priority
- Simple substring matching
- Fastest evaluation

#### Via Django Shell

```bash
python manage.py shell
```

```python
from backend.django_app.models import CategoryMapping

# Add a keyword mapping
CategoryMapping.objects.create(
    keyword="ZOMATO",
    category="lunch"
)

# View all keyword mappings
print(list(CategoryMapping.objects.all().values()))
```

#### Via API Endpoint

```bash
curl -X POST http://localhost:8000/create_category_mapping \
  -d "keyword=ZOMATO&category=lunch"
```

---

## UPI Details Extraction

### Function: `extract_upi_details(text: str)`

**Location**: [backend/fastapi_service/parser/categorizer.py](../backend/fastapi_service/parser/categorizer.py#L93-L164)

**Returns**:
```python
{
    "name": "HEMANT P",           # Uppercased, spaces collapsed
    "upi_id": "YESB/Q208692237"   # Uppercased, trailing slash removed
}
```

**Handles**:
- ✅ `TRANSFER TO 4897694162092 UPI/DR/.../HEMANT/YESB/Q731754728/...`
- ✅ `UPI/DR/.../MAYURESH/YESB/Q208692237`
- ✅ `/YESB/q208692237` (case-insensitive)
- ✅ `/YESB/q208692237/` (trailing slash variants)
- ✅ Sentence style: `"Paid to John Doe"` (fallback)
- ✅ Malformed strings (returns None safely, no crashes)

### Testing Extraction

```python
from backend.fastapi_service.parser.categorizer import extract_upi_details

description = "TRANSFER TO 4897694162092 UPI/DR/598732810891/HEMANT P/YESB/Q208692237/Payme"
details = extract_upi_details(description)
print(details)
# Output: {'name': 'HEMANT P', 'upi_id': 'YESB/Q208692237'}
```

---

## Database Management

### View All Mappings

```bash
python manage.py shell
```

```python
from backend.django_app.models import CategoryMapping, RegexCategoryMapping, AccountCategoryMapping

# Keyword mappings
print("KEYWORDS:")
for m in CategoryMapping.objects.all():
    print(f"  {m.keyword} → {m.category}")

# Regex mappings
print("\nREGEX:")
for m in RegexCategoryMapping.objects.all().order_by('priority'):
    print(f"  {m.name}: {m.pattern} → {m.category} (priority: {m.priority})")

# UPI mappings
print("\nUPI ACCOUNT:")
for m in AccountCategoryMapping.objects.all():
    print(f"  {m.upi_id} + {m.name} → {m.category}")
```

### Clear All Mappings

```bash
python manage.py shell
```

```python
from backend.django_app.models import CategoryMapping, RegexCategoryMapping, AccountCategoryMapping

CategoryMapping.objects.all().delete()
RegexCategoryMapping.objects.all().delete()
AccountCategoryMapping.objects.all().delete()
print("All mappings cleared.")
```

### Clear Transactions (Keep Mappings)

```bash
python manage.py shell
```

```python
from backend.django_app.models import Transaction, MonthlySummary, MonthlySubtypeSummary, DailyExpenseSummary

models = [Transaction, MonthlySummary, MonthlySubtypeSummary, DailyExpenseSummary]
for model in models:
    count = model.objects.count()
    model.objects.all().delete()
    print(f"Deleted {count} {model.__name__} records")
```

### Full Database Reset

```bash
python manage.py flush --noinput
python manage.py migrate
python manage.py seed_mappings
```

---

## API Endpoints Reference

### Category Mappings (Keywords)

**List all keyword mappings:**
```bash
curl http://localhost:8000/get_category_mappings
```

**Create keyword mapping:**
```bash
curl -X POST http://localhost:8000/create_category_mapping \
  -d "keyword=SWIGGY&category=lunch"
```

---

### Regex Mappings

**List all regex mappings:**
```bash
curl http://localhost:8000/get_regex_mappings
```

**Create regex mapping:**
```bash
curl -X POST http://localhost:8000/create_regex_mapping \
  -d "name=FOOD_DELIVERY&pattern=SWIGGY|ZOMATO&category=lunch&priority=2"
```

---

### Account Mappings (UPI)

**List all UPI mappings:**
```bash
curl http://localhost:8000/get_account_mappings
```

**Create UPI mapping:**
```bash
curl -X POST http://localhost:8000/create_account_mapping \
  -d "upi_id=YESB/Q731754728&name=HEMANT&category=tea&priority=1"
```

---

### Parse PDF

**Parse PDF with cached mappings:**
```bash
curl -X POST http://localhost:8000/parse-pdf \
  -F "file=@april2025.pdf"
```

**Parse with custom mappings:**
```bash
curl -X POST http://localhost:8000/parse-pdf \
  -F "file=@april2025.pdf" \
  -F 'mappings=[{"kind":"regex","name":"CUSTOM","pattern":"PATTERN","category":"lunch","priority":2}]'
```

---

## Management Commands

### Seed Default Mappings

Populates the database with seed mappings from [mapping.py](../mapping.py):

```bash
python manage.py seed_mappings
```

**Output:**
```
Default mappings seeded.
```

Edit [mapping.py](../mapping.py) to customize defaults.

---

### Create Migrations

After model changes:

```bash
python manage.py makemigrations django_app
python manage.py migrate
```

---

## Troubleshooting

### Issue: "no such table: category_mapping"

**Solution**: Run migrations:
```bash
python manage.py migrate
```

---

### Issue: "no such column: account_category_mapping.upi_id"

**Solution**: Migration out of sync. Re-apply:
```bash
python manage.py migrate
```

---

### Issue: Missing `requests` module

**Solution**: Install dependencies:
```bash
pip install -r requirements.txt
```

---

### Issue: PDF not getting categorized correctly

**Checklist**:
1. ✅ Verify mappings exist: `curl http://localhost:8000/get_account_mappings`
2. ✅ Test UPI extraction:
   ```python
   from backend.fastapi_service.parser.categorizer import extract_upi_details
   details = extract_upi_details(description)
   print(details)
   ```
3. ✅ Check transaction description matches mapping (case-sensitive for UPI ID)
4. ✅ Verify priority ranking (lower number = higher priority)

---

### Issue: Mappings not being used

**Check**:
- Is the mapping type correct for your use case?
- Is the priority correct?
- Run `python manage.py seed_mappings` to refresh cache if using in-memory caching

---

## Current Default Mappings (Seeded)

Run `python manage.py seed_mappings` to populate these:

### Keyword Rules
| Keyword | Category |
|---------|----------|
| ZOMATO  | lunch    |

### Regex Rules
| Name | Pattern | Category | Priority |
|------|---------|----------|----------|
| UPI_MAYURESH | MAYURESH | lunch | 2 |
| RECHARGE_GOOGLE | GOOGLE\|GPAYRECHAR | recharge | 2 |
| RECHARGE_PATTERNS | AIRTEL\|JIOTOP\|VODAFONE\|IDEA\|BSNL | recharge | 2 |

### UPI Account Rules
| UPI ID | Name | Category | Priority |
|--------|------|----------|----------|
| YESB/Q208692237 | MAYURESH | lunch | 1 |
| YESB/Q731754728 | HEMANT | tea | 1 |
| UTIB/GPAYRECHAR | GOOGLE I | recharge | 1 |

---

## Managing Seeded Mappings

Choose from these when creating mappings:

```
"cash_withdrawal"    # ATM withdrawals
"extra"              # Miscellaneous expenses
"lunch"              # Food delivery, restaurants
"other"              # Unclassified (default)
"recharge"           # Mobile/DTH recharge
"tea"                # Beverages, snacks
"credit"             # Credit/refund transactions
```

---

## Example: Complete Workflows

### Example 1: Lunch Categorization (MAYURESH)

**Scenario**: Categorize all transactions from "MAYURESH"

**Step 1: Identify the transaction format**
```
TRANSFER TO 1234567890 UPI/DR/987654321/MAYURESH/YESB/Q208692237/Payment
```

**Step 2: Extract UPI details**
```
name: "MAYURESH"
upi_id: "YESB/Q208692237"
```

**Step 3: Create UPI mapping** (already seeded by default)
```bash
python manage.py shell
```

```python
from backend.django_app.models import AccountCategoryMapping

AccountCategoryMapping.objects.create(
    upi_id="YESB/Q208692237",
    name="MAYURESH",
    category="lunch",
    priority=1
)
```

**Step 4: Verify in database**
```python
mapping = AccountCategoryMapping.objects.get(upi_id="YESB/Q208692237")
print(f"{mapping.upi_id} + {mapping.name} → {mapping.category}")
# Output: YESB/Q208692237 + MAYURESH → lunch
```

---

### Example 2: Recharge Categorization (Google Pay)

**Scenario**: Categorize Google Pay recharge transactions

**Transaction format**:
```
TRANSFER TO 4897691162095 UPI/DR/510436257862/Google I/UTIB/gpayrechar/UPI
```

**Extracted**:
```
name: "GOOGLE I"
upi_id: "UTIB/GPAYRECHAR"
```

**Mapping** (already seeded by default):
```python
AccountCategoryMapping.objects.create(
    upi_id="UTIB/GPAYRECHAR",
    name="GOOGLE I",
    category="recharge",
    priority=1
)
```

**Result**: All Google Pay recharge transactions automatically tagged as "recharge"

---

### Example 3: Add Another Telecom Provider

**Scenario**: Add support for Airtel One recharge

**Step 1: Collect sample transaction**
```
TRANSFER TO 5234567890 UPI/DR/123456789/AIRTEL ONE/ICIC/Q987654321/Recharge
```

**Step 2: Extract and create mapping**
```python
from backend.django_app.models import AccountCategoryMapping

AccountCategoryMapping.objects.create(
    upi_id="ICIC/Q987654321",
    name="AIRTEL ONE",
    category="recharge",
    priority=1
)

# Or add to mapping.py for seeding:
# Edit mapping.py and add to seed_default_mappings():
AccountCategoryMapping.objects.get_or_create(
    upi_id="ICIC/Q987654321",
    name="AIRTEL ONE",
    defaults={"category": "recharge", "priority": 1}
)
```

**Step 3: Reseed if needed**
```bash
python manage.py seed_mappings
```

---

## Notes

- **UPI mappings take precedence** over regex and keyword rules
- **Regex priority**: Lower numbers checked first (priority 1 before priority 100)
- **Name normalization**: All receiver names are uppercased and stored without special characters
- **UPI ID format**: Always `BANK/REFERENCE`, both uppercased, trailing slashes removed
- **Cache invalidation**: Mapped transaction parsing uses a 120-second cache; manual API calls hit fresh data

---

**Last Updated**: March 31, 2026
