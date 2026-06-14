# Import Path Fix - Reference Guide

## Problem
When running `python ml/training/train_hurdle.py`, Python couldn't find the `ml` module:
```
ModuleNotFoundError: No module named 'ml'
```

## Root Cause
Python's import resolution didn't know about the project root directory when scripts imported modules like:
```python
from ml.artifacts import ...
from backend.django_app.models import ...
```

## Solution Applied
Added automatic path resolution at the top of each module:

```python
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent  # or .parent.parent
sys.path.insert(0, str(project_root))

# Now imports work:
from ml.artifacts import ...
from backend.django_app.models import ...
```

## Files Fixed
1. `ml/training/train_hurdle.py` — Added path setup (parent.parent.parent)
2. `ml/inference/hurdle_forecast.py` — Added path setup (parent.parent.parent)
3. `ml/active_learning.py` — Added path setup (parent.parent)
4. `ml/experiment_reporting.py` — Added path setup (parent.parent)

## Testing the Fix
All scripts now run successfully from project root:
```bash
cd "d:\M Projects\BrainIQ"
python ml/training/train_hurdle.py          ✓ Works
python ml/experiment_reporting.py           ✓ Works
python ml/active_learning.py --report       ✓ Works
python validate_implementations.py          ✓ Works
```

## How Path Resolution Works
Each script calculates the project root based on its own location:

**For scripts at `ml/training/train_hurdle.py`:**
```
__file__ → D:\M Projects\BrainIQ\ml\training\train_hurdle.py
.resolve() → Full absolute path
.parent → D:\M Projects\BrainIQ\ml\training
.parent.parent.parent → D:\M Projects\BrainIQ  ← project_root
```

**For scripts at `ml/active_learning.py`:**
```
__file__ → D:\M Projects\BrainIQ\ml\active_learning.py
.parent.parent → D:\M Projects\BrainIQ  ← project_root
```

This way, any script can find imports correctly regardless of where Python is invoked from.

## Alternative Approaches (Not Used)
1. Run with `-m`: `python -m ml.training.train_hurdle` — More complex setup
2. Add to PYTHONPATH: Environment variable approach — Less portable
3. setup.py install: Requires package installation — Overkill for dev
4. Relative imports: Less explicit, harder to debug

## Final Result
✅ All modules can be imported correctly
✅ Scripts run from project root
✅ Path resolution is automatic
✅ No environment variables needed
✅ Portable across Windows/Linux/Mac
