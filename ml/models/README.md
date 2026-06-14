# ML Models

Saved model artifacts are written here.

Expected files:

- `transaction_classifier.joblib`
- `transaction_vectorizer.joblib`
- `transaction_classifier.manifest.json`
- `transaction_classifier.<version>.joblib`
- `transaction_vectorizer.<version>.joblib`
- `transaction_classifier.<version>.metrics.json`
- `daily_spend_regressor.joblib`
- `daily_spend_regressor.manifest.json`
- `daily_spend_regressor.<version>.joblib`
- `daily_spend_regressor.<version>.metrics.json`

The manifest is the source of truth for the latest promoted model version. The unversioned files are kept for backward compatibility with existing tooling.
