from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split

from .features import model_matrix


def train_model(features: pd.DataFrame, output: str | Path = "artifacts/model.joblib", seed: int = 42) -> dict:
    y = features["is_fraud"].astype(int)
    train_frame, test_frame, y_train, y_test = train_test_split(features, y, test_size=0.25, stratify=y, random_state=seed)
    from .features import engineer_features

    train_features = engineer_features(train_frame.reset_index(drop=True))
    test_features = engineer_features(test_frame.reset_index(drop=True), history=train_frame.reset_index(drop=True))
    # Feature engineering sorts rows; keep labels aligned with that sorted order.
    y_train = train_features["is_fraud"].astype(int)
    y_test = test_features["is_fraud"].astype(int)
    x_train, x_test = model_matrix(train_features), model_matrix(test_features)
    classifier = HistGradientBoostingClassifier(max_iter=160, learning_rate=0.08, max_leaf_nodes=15, random_state=seed, class_weight="balanced")
    classifier.fit(x_train, y_train)
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": classifier, "features": list(x_train.columns), "version": "0.1.0"}, path)
    probabilities = classifier.predict_proba(x_test)[:, 1]
    metrics = evaluate_predictions(y_test, probabilities)
    metrics["model_path"] = str(path)
    return metrics


def load_model(path: str | Path = "artifacts/model.joblib") -> dict:
    return joblib.load(path)


def predict_probability(bundle: dict, features: pd.DataFrame) -> float:
    return float(bundle["model"].predict_proba(model_matrix(features)[bundle["features"]])[:, 1][0])


def evaluate_predictions(actual: pd.Series, probabilities: pd.Series, threshold: float = 0.5) -> dict:
    predicted = (probabilities >= threshold).astype(int)
    return {
        "precision": float(precision_score(actual, predicted, zero_division=0)),
        "recall": float(recall_score(actual, predicted, zero_division=0)),
        "f1": float(f1_score(actual, predicted, zero_division=0)),
        "average_precision": float(average_precision_score(actual, probabilities)),
        "roc_auc": float(roc_auc_score(actual, probabilities)),
        "confusion_matrix": confusion_matrix(actual, predicted).tolist(),
    }
