from __future__ import annotations

import argparse
import csv
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from backend.config.settings import settings
from backend.utils.preprocessing import normalize_text


def train_model(dataset_path: Path, model_path: Path, vectorizer_path: Path) -> int:
    texts: list[str] = []
    labels: list[str] = []

    with dataset_path.open('r', encoding='utf-8', newline='') as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            text = normalize_text(f"{row.get('counterparty', '')} {row.get('text', '')}")
            category = normalize_text(row.get('category', ''))
            if text and category:
                texts.append(text)
                labels.append(category)

    if not texts:
        raise ValueError('Training dataset is empty. Run ml/preprocessing/build_dataset.py after importing transactions.')

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, strip_accents='unicode')
    model = LogisticRegression(max_iter=300, class_weight='balanced')
    features = vectorizer.fit_transform(texts)
    model.fit(features, labels)

    model_path.parent.mkdir(parents=True, exist_ok=True)
    vectorizer_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    joblib.dump(vectorizer, vectorizer_path)
    return len(texts)


def main() -> None:
    parser = argparse.ArgumentParser(description='Train a TF-IDF + Logistic Regression transaction classifier.')
    parser.add_argument('--dataset', default='ml/data/training_dataset.csv', help='CSV dataset path')
    parser.add_argument('--model-path', default=str(settings.model_path), help='Joblib output for the classifier')
    parser.add_argument('--vectorizer-path', default=str(settings.vectorizer_path), help='Joblib output for the vectorizer')
    args = parser.parse_args()

    rows = train_model(
        dataset_path=Path(args.dataset),
        model_path=Path(args.model_path),
        vectorizer_path=Path(args.vectorizer_path),
    )
    print(f'Trained classifier on {rows} labeled transactions')


if __name__ == '__main__':
    main()
