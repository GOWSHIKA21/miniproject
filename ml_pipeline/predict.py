"""Inference and Prediction Utility for Trained Patent ML Models.
Provides domain classification, prosecution pendency forecasting, and
unsupervised cluster assignment for new patent queries and titles.
"""

import os
import argparse
import joblib
import json
import logging
from typing import Dict, Any, List
import numpy as np

import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class PatentPredictor:
    """Inference engine combining all trained ML pipeline models."""

    def __init__(self):
        self._load_models()

    def _load_models(self):
        if not config.BEST_CLASSIFIER_PATH.exists():
            raise FileNotFoundError(f"Model not found at {config.BEST_CLASSIFIER_PATH}. Run pipeline first.")

        self.classifier = joblib.load(config.BEST_CLASSIFIER_PATH)
        self.vectorizer = joblib.load(config.TFIDF_VECTORIZER_PATH)
        self.label_encoder = joblib.load(config.LABEL_ENCODER_PATH)

        self.regressor_artifact = None
        if config.PENDENCY_REGRESSOR_PATH.exists():
            self.regressor_artifact = joblib.load(config.PENDENCY_REGRESSOR_PATH)

        self.cluster_artifact = None
        if config.KMEANS_MODEL_PATH.exists():
            self.cluster_artifact = joblib.load(config.KMEANS_MODEL_PATH)

    def predict(
        self,
        title: str,
        ipo_location: str = "Delhi",
        application_type: str = "ORDINARY APPLICATION",
        pages: int = 25,
        claims: int = 15,
        filing_year: int = 2024
    ) -> Dict[str, Any]:
        """Predict domain, pendency, and cluster for a patent title."""
        clean_title = title.strip().lower()
        X_tfidf = self.vectorizer.transform([clean_title])

        # 1. Classification & Probabilities
        if hasattr(self.classifier, "predict_proba"):
            probs = self.classifier.predict_proba(X_tfidf)[0]
        elif hasattr(self.classifier, "decision_function"):
            df_scores = self.classifier.decision_function(X_tfidf)[0]
            # Softmax approximation
            exp_scores = np.exp(df_scores - np.max(df_scores))
            probs = exp_scores / exp_scores.sum()
        else:
            probs = np.zeros(len(self.label_encoder.classes_))
            pred_idx = self.classifier.predict(X_tfidf)[0]
            probs[pred_idx] = 1.0

        top_indices = np.argsort(probs)[::-1][:3]
        top_predictions = [
            {
                "domain": str(self.label_encoder.classes_[idx]),
                "confidence": round(float(probs[idx]), 4)
            }
            for idx in top_indices
        ]

        best_domain = top_predictions[0]["domain"]
        best_confidence = top_predictions[0]["confidence"]

        # 2. Pendency Regression
        estimated_pendency = None
        if self.regressor_artifact:
            try:
                from scipy.sparse import hstack, csr_matrix
                ohe = self.regressor_artifact["one_hot_encoder"]
                scaler = self.regressor_artifact["scaler"]
                reg_model = self.regressor_artifact["model"]

                import pandas as pd
                cat_cols = self.regressor_artifact["cat_cols"]
                num_cols = self.regressor_artifact["num_cols"]
                df_cat = pd.DataFrame([[ipo_location, best_domain, application_type]], columns=cat_cols)
                df_num = pd.DataFrame([[pages, claims, filing_year]], columns=num_cols)
                cat_input = ohe.transform(df_cat)
                num_input = scaler.transform(df_num)
                X_full = hstack([X_tfidf, cat_input, csr_matrix(num_input)]).tocsr()

                pred_days = float(reg_model.predict(X_full)[0])
                pred_days = max(180, pred_days)  # Minimum realistic pendency
                estimated_pendency = {
                    "estimated_days": round(pred_days, 1),
                    "estimated_months": round(pred_days / 30.4, 1),
                    "estimated_years": round(pred_days / 365.25, 2)
                }
            except Exception as e:
                logger.warning(f"Could not compute pendency regression: {e}")

        # 3. Cluster Assignment
        cluster_info = None
        if self.cluster_artifact:
            try:
                svd = self.cluster_artifact["svd"]
                kmeans = self.cluster_artifact["kmeans"]
                summaries = self.cluster_artifact["cluster_summaries"]

                X_svd = svd.transform(X_tfidf)
                cluster_idx = int(kmeans.predict(X_svd)[0])
                matched_summary = summaries[cluster_idx] if cluster_idx < len(summaries) else None

                cluster_info = {
                    "cluster_id": cluster_idx + 1,
                    "theme": matched_summary["theme_label"] if matched_summary else f"Cluster {cluster_idx + 1}",
                    "top_keywords": matched_summary["top_keywords"] if matched_summary else []
                }
            except Exception as e:
                logger.warning(f"Could not assign cluster: {e}")

        return {
            "title": title,
            "predicted_domain": best_domain,
            "confidence": best_confidence,
            "top_3_domains": top_predictions,
            "estimated_prosecution_pendency": estimated_pendency,
            "thematic_cluster": cluster_info
        }


def main():
    parser = argparse.ArgumentParser(description="Predict patent domain, pendency, and cluster.")
    parser.add_argument("--title", type=str, required=True, help="Patent title to classify")
    parser.add_argument("--location", type=str, default="Delhi", help="IPO location (Delhi, Chennai, Kolkata, Mumbai)")
    parser.add_argument("--type", type=str, default="ORDINARY APPLICATION", help="Application type")
    parser.add_argument("--claims", type=int, default=15, help="Number of claims")
    parser.add_argument("--pages", type=int, default=25, help="Number of pages")
    parser.add_argument("--year", type=int, default=2024, help="Filing year")
    args = parser.parse_args()

    predictor = PatentPredictor()
    result = predictor.predict(
        title=args.title,
        ipo_location=args.location,
        application_type=args.type,
        claims=args.claims,
        pages=args.pages,
        filing_year=args.year
    )

    print("\n" + "=" * 60)
    print(" PATENT ML INFERENCE REPORT")
    print("=" * 60)
    print(f"Title: {result['title']}")
    print(f"\n[Domain Classification]")
    print(f"  Primary Prediction: {result['predicted_domain']} (Confidence: {result['confidence'] * 100:.1f}%)")
    print("  Alternative Probabilities:")
    for alt in result["top_3_domains"]:
        print(f"    - {alt['domain']:<15}: {alt['confidence'] * 100:.2f}%")

    if result["estimated_prosecution_pendency"]:
        pend = result["estimated_prosecution_pendency"]
        print(f"\n[Prosecution Pendency Forecast]")
        print(f"  Estimated Grant Duration: {pend['estimated_months']} months (~{pend['estimated_years']} years / {pend['estimated_days']} days)")

    if result["thematic_cluster"]:
        clust = result["thematic_cluster"]
        print(f"\n[Thematic Cluster Assignment]")
        print(f"  {clust['theme']}")
        print(f"  Associated Keywords: {', '.join(clust['top_keywords'])}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
