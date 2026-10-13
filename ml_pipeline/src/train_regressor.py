"""Patent Pendency and Examination Regression Training Module.
Predicts prosecution pendency duration (filing-to-grant latency in days)
using invention text semantics and patent prosecution metadata.
"""

import os
import json
import joblib
import logging
import time
from typing import Dict, Any
import numpy as np
import pandas as pd
from scipy.sparse import hstack
from sklearn.linear_model import Ridge
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def train_pendency_regressor(feature_data: Dict[str, Any]) -> Dict[str, Any]:
    """Train and evaluate regression models on patent pendency duration (days)."""
    train_df = feature_data["train_df"]
    val_df = feature_data["val_df"]
    test_df = feature_data["test_df"]
    tfidf = feature_data["tfidf_vectorizer"]

    logger.info("Preparing data for patent prosecution pendency regression...")

    # Filter rows having valid pendency_days
    tr = train_df.dropna(subset=["pendency_days"]).copy()
    va = val_df.dropna(subset=["pendency_days"]).copy()
    te = test_df.dropna(subset=["pendency_days"]).copy()

    logger.info(f"Filtered valid pendency records: Train={len(tr):,}, Val={len(va):,}, Test={len(te):,}")

    y_train = tr["pendency_days"].values
    y_val = va["pendency_days"].values
    y_test = te["pendency_days"].values

    # Categorical metadata one-hot encoding
    cat_cols = ["ipo_location", "field_of_invention", "application_type"]
    ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=True)
    X_train_cat = ohe.fit_transform(tr[cat_cols])
    X_val_cat = ohe.transform(va[cat_cols])
    X_test_cat = ohe.transform(te[cat_cols])

    # Numerical scaling
    num_cols = ["no_of_pages_imputed", "no_of_claims_imputed", "filing_year"]
    scaler = StandardScaler()
    X_train_num = scaler.fit_transform(tr[num_cols].fillna(0))
    X_val_num = scaler.transform(va[num_cols].fillna(0))
    X_test_num = scaler.transform(te[num_cols].fillna(0))

    # Text TF-IDF features
    X_train_text = tfidf.transform(tr[config.TEXT_COLUMN])
    X_val_text = tfidf.transform(va[config.TEXT_COLUMN])
    X_test_text = tfidf.transform(te[config.TEXT_COLUMN])

    # Stack sparse feature matrices
    from scipy.sparse import csr_matrix
    X_train_full = hstack([X_train_text, X_train_cat, csr_matrix(X_train_num)]).tocsr()
    X_val_full = hstack([X_val_text, X_val_cat, csr_matrix(X_val_num)]).tocsr()
    X_test_full = hstack([X_test_text, X_test_cat, csr_matrix(X_test_num)]).tocsr()

    logger.info(f"Regression feature matrix shape: {X_train_full.shape}")

    models = {
        "Ridge_Regression": Ridge(alpha=10.0, random_state=config.RANDOM_SEED),
    }

    trained_regressors = {}
    metrics = {}

    for name, model in models.items():
        logger.info(f"--> Training {name}...")
        t0 = time.time()
        model.fit(X_train_full, y_train)
        duration = time.time() - t0

        val_preds = model.predict(X_val_full)
        mae = float(mean_absolute_error(y_val, val_preds))
        rmse = float(np.sqrt(mean_squared_error(y_val, val_preds)))
        r2 = float(r2_score(y_val, val_preds))

        logger.info(f"    [{name}] Val MAE: {mae:.1f} days ({mae/30.4:.1f} months) | RMSE: {rmse:.1f} | R²: {r2:.4f}")

        trained_regressors[name] = model
        metrics[name] = {
            "val_mae_days": round(mae, 2),
            "val_mae_months": round(mae / 30.4, 2),
            "val_rmse": round(rmse, 2),
            "val_r2": round(r2, 4),
            "training_time_seconds": round(duration, 2)
        }

    # Best model evaluation on Test set
    best_name = "Ridge_Regression"
    best_reg = trained_regressors[best_name]

    test_preds = best_reg.predict(X_test_full)
    test_mae = float(mean_absolute_error(y_test, test_preds))
    test_rmse = float(np.sqrt(mean_squared_error(y_test, test_preds)))
    test_r2 = float(r2_score(y_test, test_preds))

    logger.info(f"\n=== Test Set Regression ({best_name}) ===")
    logger.info(f"Test MAE:  {test_mae:.1f} days ({test_mae/30.4:.1f} months)")
    logger.info(f"Test RMSE: {test_rmse:.1f} days")
    logger.info(f"Test R²:   {test_r2:.4f}")

    # Save artifact bundle
    artifact = {
        "model": best_reg,
        "one_hot_encoder": ohe,
        "scaler": scaler,
        "cat_cols": cat_cols,
        "num_cols": num_cols
    }
    joblib.dump(artifact, config.PENDENCY_REGRESSOR_PATH)
    logger.info(f"Saved pendency regressor to {config.PENDENCY_REGRESSOR_PATH}")

    regression_report = {
        "target": "pendency_days",
        "description": "Filing to Grant publication duration in days",
        "models_evaluated": metrics,
        "test_evaluation": {
            "test_mae_days": round(test_mae, 2),
            "test_mae_months": round(test_mae / 30.4, 2),
            "test_rmse_days": round(test_rmse, 2),
            "test_r2": round(test_r2, 4)
        }
    }

    with open(config.REGRESSION_METRICS_JSON, "w", encoding="utf-8") as f:
        json.dump(regression_report, f, indent=2)
    logger.info(f"Saved regression metrics to {config.REGRESSION_METRICS_JSON}")

    return regression_report


if __name__ == "__main__":
    from feature_engineering import prepare_features_and_splits
    features = prepare_features_and_splits(sample_limit=15000)
    train_pendency_regressor(features)
