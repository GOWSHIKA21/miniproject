"""Patent Domain Multi-Class Classification Training Module.
Trains, validates, and compares multiple NLP classifiers (MultinomialNB, Logistic Regression,
Linear SVM / SGD, Calibrated Classifier), benchmarks metrics, and saves the best model.
"""

import os
import time
import json
import joblib
import logging
from typing import Dict, Any, List
import numpy as np
import pandas as pd
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix
)

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def train_and_evaluate_classifiers(
    feature_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Train multiple classifiers, compare validation performance, and evaluate best model on test set."""
    X_train = feature_data["X_train_tfidf"]
    y_train = feature_data["y_train"]
    X_val = feature_data["X_val_tfidf"]
    y_val = feature_data["y_val"]
    X_test = feature_data["X_test_tfidf"]
    y_test = feature_data["y_test"]
    classes = feature_data["classes"]

    logger.info(f"Training multi-class classifiers over {len(classes)} classes...")
    logger.info(f"Training shape: {X_train.shape}, Val shape: {X_val.shape}, Test shape: {X_test.shape}")

    # Define candidate models
    models = {
        "Multinomial_Naive_Bayes": MultinomialNB(alpha=0.1),
        "Logistic_Regression": LogisticRegression(
            C=2.0,
            max_iter=500,
            solver="lbfgs",
            random_state=config.RANDOM_SEED
        ),
        "Linear_SVM_Calibrated": CalibratedClassifierCV(
            LinearSVC(C=1.0, max_iter=2000, random_state=config.RANDOM_SEED),
            cv=3
        ),
        "SGD_Classifier": SGDClassifier(
            loss="modified_huber",
            alpha=1e-4,
            max_iter=1000,
            random_state=config.RANDOM_SEED
        )
    }

    trained_models = {}
    validation_results = {}
    best_model_name = None
    best_val_f1 = -1.0

    for name, model in models.items():
        logger.info(f"--> Training {name}...")
        start_time = time.time()
        model.fit(X_train, y_train)
        train_duration = time.time() - start_time

        # Predict on validation split
        val_preds = model.predict(X_val)

        acc = float(accuracy_score(y_val, val_preds))
        macro_f1 = float(f1_score(y_val, val_preds, average="macro"))
        weighted_f1 = float(f1_score(y_val, val_preds, average="weighted"))
        precision = float(precision_score(y_val, val_preds, average="weighted", zero_division=0))
        recall = float(recall_score(y_val, val_preds, average="weighted", zero_division=0))

        logger.info(f"    [{name}] Val Acc: {acc:.4f} | Weighted F1: {weighted_f1:.4f} | Time: {train_duration:.2f}s")

        trained_models[name] = model
        validation_results[name] = {
            "validation_accuracy": round(acc, 4),
            "macro_f1": round(macro_f1, 4),
            "weighted_f1": round(weighted_f1, 4),
            "weighted_precision": round(precision, 4),
            "weighted_recall": round(recall, 4),
            "training_time_seconds": round(train_duration, 2)
        }

        if weighted_f1 > best_val_f1:
            best_val_f1 = weighted_f1
            best_model_name = name

    logger.info(f"\nBest Model on Validation: {best_model_name} (Weighted F1: {best_val_f1:.4f})")
    best_model = trained_models[best_model_name]

    # Evaluate Best Model on Unseen Test Split
    test_preds = best_model.predict(X_test)
    test_acc = float(accuracy_score(y_test, test_preds))
    test_macro_f1 = float(f1_score(y_test, test_preds, average="macro"))
    test_weighted_f1 = float(f1_score(y_test, test_preds, average="weighted"))
    test_precision = float(precision_score(y_test, test_preds, average="weighted", zero_division=0))
    test_recall = float(recall_score(y_test, test_preds, average="weighted", zero_division=0))

    report_str = classification_report(y_test, test_preds, target_names=classes, zero_division=0)
    conf_matrix = confusion_matrix(y_test, test_preds).tolist()

    logger.info(f"\n=== Test Set Performance ({best_model_name}) ===")
    logger.info(f"Test Accuracy:    {test_acc:.4f}")
    logger.info(f"Test Weighted F1: {test_weighted_f1:.4f}")
    logger.info(f"Test Macro F1:    {test_macro_f1:.4f}")

    # Persist Best Model and All Models
    joblib.dump(best_model, config.BEST_CLASSIFIER_PATH)
    joblib.dump(trained_models, config.ALL_CLASSIFIERS_PATH)
    logger.info(f"Saved best classifier to {config.BEST_CLASSIFIER_PATH}")
    logger.info(f"Saved all trained models to {config.ALL_CLASSIFIERS_PATH}")

    # Write textual classification report
    report_file = config.REPORTS_DIR / "classification_report.txt"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(f"BEST MODEL: {best_model_name}\n")
        f.write(f"TEST ACCURACY: {test_acc:.4f}\n")
        f.write(f"TEST WEIGHTED F1: {test_weighted_f1:.4f}\n\n")
        f.write("DETAILED PER-CLASS CLASSIFICATION REPORT:\n")
        f.write(report_str)

    # Save comprehensive JSON metrics
    metrics_summary = {
        "best_model": best_model_name,
        "models_benchmarked": validation_results,
        "test_evaluation": {
            "test_accuracy": round(test_acc, 4),
            "test_macro_f1": round(test_macro_f1, 4),
            "test_weighted_f1": round(test_weighted_f1, 4),
            "test_precision": round(test_precision, 4),
            "test_recall": round(test_recall, 4),
        },
        "target_classes": classes,
        "confusion_matrix": conf_matrix
    }

    with open(config.CLASSIFICATION_METRICS_JSON, "w", encoding="utf-8") as f:
        json.dump(metrics_summary, f, indent=2)
    logger.info(f"Saved classification metrics to {config.CLASSIFICATION_METRICS_JSON}")

    return {
        "best_model_name": best_model_name,
        "best_model": best_model,
        "test_metrics": metrics_summary["test_evaluation"],
        "validation_results": validation_results,
        "confusion_matrix": np.array(conf_matrix),
        "classes": classes
    }


if __name__ == "__main__":
    from feature_engineering import prepare_features_and_splits
    features = prepare_features_and_splits()
    results = train_and_evaluate_classifiers(features)
    print("\nTraining completed successfully!")
