# ML Pipeline

## Objective

Input: transaction text such as `Paid to mess`

Output: spending category such as `mess` or `food`

## Current Design

1. Import labeled transactions into the normalized database.
2. Export them with `ml/preprocessing/build_dataset.py` into `ml/data/training_dataset.csv`.
3. Train a baseline classifier with `ml/training/train_classifier.py`.
4. Save TF-IDF and Logistic Regression artifacts into `ml/models/`.
5. Use `ml/inference/predict.py` or the backend hybrid categorizer for prediction.

## Modeling Strategy

- Baseline: TF-IDF + Logistic Regression
- Why: fast to train, interpretable, works well on short merchant text
- Fallback: deterministic rules remain the first layer for known merchants and categories
- Future upgrade: sentence embeddings or BERT-style classifiers for better semantic coverage

## Recommended Future Enhancements

- Add active learning from manually corrected categories.
- Track model version and confidence scores per prediction.
- Split training data by month to detect concept drift.
- Introduce evaluation metrics before promoting a new model artifact.
