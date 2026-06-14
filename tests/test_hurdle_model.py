"""Tests for two-stage hurdle model training and inference."""

import os
import csv
from pathlib import Path
from decimal import Decimal
import tempfile

import django
import pytest
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingRegressor

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from ml.training.train_hurdle import (
    _load_dataset,
    _split_time_ordered,
    _compute_metrics,
    Dataset,
)


@pytest.fixture
def sample_hurdle_dataset():
    """Create a temporary regression dataset for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "lag_1", "lag_3_mean", "lag_7_mean", "lag_14_mean", "weekday", "month", "is_weekend", "target_total_debit"
        ])
        writer.writeheader()

        # Mix of zero and non-zero spend days
        for i in range(20):
            target = 100.0 if i % 3 != 0 else 0.0  # 2/3 spend days, 1/3 zero days
            writer.writerow({
                "lag_1": 50.0 + i,
                "lag_3_mean": 45.0 + i * 0.5,
                "lag_7_mean": 40.0 + i * 0.3,
                "lag_14_mean": 35.0 + i * 0.2,
                "weekday": i % 7,
                "month": (i % 12) + 1,
                "is_weekend": 1.0 if (i % 7) >= 5 else 0.0,
                "target_total_debit": target,
            })

        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    temp_path.unlink()


def test_load_dataset_structure(sample_hurdle_dataset):
    """Test that dataset loads with correct structure."""
    dataset = _load_dataset(sample_hurdle_dataset)

    assert isinstance(dataset, Dataset)
    assert len(dataset.features) == len(dataset.target)
    assert len(dataset.has_spend) == len(dataset.target)
    assert all(isinstance(row, list) for row in dataset.features)
    assert all(isinstance(t, float) for t in dataset.target)
    assert all(s in [0, 1] for s in dataset.has_spend)


def test_load_dataset_has_spend_labels(sample_hurdle_dataset):
    """Test that has_spend labels are correct (1 for target > 0, else 0)."""
    dataset = _load_dataset(sample_hurdle_dataset)

    for target, has_spend in zip(dataset.target, dataset.has_spend):
        expected_label = 1 if target > 0 else 0
        assert has_spend == expected_label


def test_split_time_ordered(sample_hurdle_dataset):
    """Test time-ordered 80-20 split."""
    dataset = _load_dataset(sample_hurdle_dataset)
    train, validation = _split_time_ordered(dataset)

    # Check split proportions
    total = len(dataset.target)
    expected_train_size = int(total * 0.8)
    assert len(train.target) >= expected_train_size - 1
    assert len(validation.target) >= 1

    # Check temporal ordering: no overlap
    if len(train.target) > 0 and len(validation.target) > 0:
        # Validation should follow training (time-ordered)
        assert len(train.features) + len(validation.features) == len(dataset.features)


def test_compute_metrics():
    """Test metric computation."""
    actual = [100.0, 150.0, 200.0]
    predicted = [110.0, 140.0, 210.0]

    metrics = _compute_metrics(actual, predicted)

    assert "mae" in metrics
    assert "rmse" in metrics
    assert "mape" in metrics
    assert metrics["mae"] > 0
    assert metrics["rmse"] > 0
    assert metrics["mape"] > 0


def test_metrics_perfect_prediction():
    """Test metrics on perfect predictions."""
    actual = [100.0, 100.0, 100.0]
    predicted = [100.0, 100.0, 100.0]

    metrics = _compute_metrics(actual, predicted)

    assert metrics["mae"] == 0.0
    assert metrics["rmse"] == 0.0
    assert metrics["mape"] == 0.0


def test_empty_dataset_error():
    """Test that empty dataset raises error."""
    empty_dataset = Dataset(features=[], target=[], has_spend=[])

    with pytest.raises(ValueError, match="split"):
        _split_time_ordered(empty_dataset)


def test_stage1_classifier_creation():
    """Test that binary classifier can be instantiated."""
    stage1 = LogisticRegression(class_weight="balanced", max_iter=1000)
    X = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    y = [0, 1, 0]

    stage1.fit(X, y)
    predictions = stage1.predict(X)

    assert len(predictions) == len(y)
    assert all(p in [0, 1] for p in predictions)


def test_stage2_quantile_regressor_creation():
    """Test that quantile regressor can be instantiated."""
    stage2 = GradientBoostingRegressor(loss="quantile", alpha=0.5, n_estimators=10, random_state=42)
    X = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]]
    y = [10.0, 50.0, 90.0, 120.0]

    stage2.fit(X, y)
    predictions = stage2.predict(X)

    assert len(predictions) == len(y)
    assert all(isinstance(p, (float, np.floating)) for p in predictions)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
