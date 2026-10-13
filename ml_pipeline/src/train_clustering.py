"""Unsupervised Patent Technology Clustering and Thematic Discovery Module.
Discovers latent technological domains and emerging research clusters using
Latent Semantic Analysis (TruncatedSVD) and MiniBatchKMeans clustering.
"""

import os
import json
import joblib
import logging
import time
from typing import Dict, Any, List
import numpy as np
import pandas as pd
from sklearn.decomposition import TruncatedSVD
from sklearn.cluster import MiniBatchKMeans

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def train_patent_clustering(
    feature_data: Dict[str, Any],
    num_clusters: int = config.KMEANS_CLUSTERS,
    n_components: int = 50
) -> Dict[str, Any]:
    """Train unsupervised LSA + MiniBatchKMeans clustering and extract topical keywords."""
    X_train = feature_data["X_train_tfidf"]
    tfidf = feature_data["tfidf_vectorizer"]
    terms = np.array(tfidf.get_feature_names_out())

    logger.info(f"Running Unsupervised Latent Semantic Analysis (TruncatedSVD dim={n_components})...")
    svd = TruncatedSVD(n_components=n_components, random_state=config.RANDOM_SEED)
    X_svd = svd.fit_transform(X_train)
    explained_var = float(svd.explained_variance_ratio_.sum())
    logger.info(f"SVD total explained variance: {explained_var:.2%}")

    logger.info(f"Training MiniBatchKMeans with k={num_clusters} technology clusters...")
    t0 = time.time()
    kmeans = MiniBatchKMeans(
        n_clusters=num_clusters,
        batch_size=1024,
        random_state=config.RANDOM_SEED,
        max_iter=100
    )
    cluster_labels = kmeans.fit_predict(X_svd)
    clustering_time = time.time() - t0

    # Project cluster centroids back to TF-IDF feature space to extract representative terms
    cluster_centroids_tfidf = svd.inverse_transform(kmeans.cluster_centers_)

    cluster_summaries = []
    top_n_terms = 8

    logger.info("\n=== Latent Patent Technology Clusters Discovered ===")
    for c_id in range(num_clusters):
        top_indices = cluster_centroids_tfidf[c_id].argsort()[::-1][:top_n_terms]
        top_keywords = [str(terms[idx]) for idx in top_indices]
        cluster_size = int((cluster_labels == c_id).sum())
        percentage = (cluster_size / len(cluster_labels)) * 100

        theme_label = f"Cluster {c_id + 1}: {', '.join(top_keywords[:3]).title()}"
        logger.info(f"[{theme_label}] ({cluster_size:,} patents, {percentage:.1f}%)")
        logger.info(f"   Keywords: {', '.join(top_keywords)}")

        cluster_summaries.append({
            "cluster_id": c_id + 1,
            "theme_label": theme_label,
            "size": cluster_size,
            "percentage": round(percentage, 2),
            "top_keywords": top_keywords
        })

    # Save cluster artifacts
    cluster_artifact = {
        "kmeans": kmeans,
        "svd": svd,
        "cluster_summaries": cluster_summaries,
        "num_clusters": num_clusters
    }
    joblib.dump(cluster_artifact, config.KMEANS_MODEL_PATH)
    logger.info(f"Saved clustering artifact to {config.KMEANS_MODEL_PATH}")

    clustering_report = {
        "num_clusters": num_clusters,
        "svd_components": n_components,
        "explained_variance_ratio": round(explained_var, 4),
        "inertia": float(kmeans.inertia_),
        "clustering_time_seconds": round(clustering_time, 2),
        "clusters": cluster_summaries
    }

    with open(config.CLUSTERING_SUMMARY_JSON, "w", encoding="utf-8") as f:
        json.dump(clustering_report, f, indent=2)
    logger.info(f"Saved clustering summary to {config.CLUSTERING_SUMMARY_JSON}")

    return clustering_report


if __name__ == "__main__":
    from feature_engineering import prepare_features_and_splits
    features = prepare_features_and_splits(sample_limit=15000)
    train_patent_clustering(features)
