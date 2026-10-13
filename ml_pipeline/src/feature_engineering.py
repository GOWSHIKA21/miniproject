"""Feature Engineering and Train/Val/Test Split Module.
Handles stratified data partitioning, TF-IDF n-gram text vectorization,
label encoding, metadata transformations, and persistence of vectorizers.
"""

import os
import joblib
import logging
from typing import Tuple, Dict, Any, Optional
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder, StandardScaler

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def prepare_features_and_splits(
    data_parquet_path: str = str(config.CLEANED_DATA_PARQUET),
    sample_limit: Optional = None
) -> Dict[str, Any]:
    """Partition dataset into train/val/test splits, vectorize text features, and encode targets."""
    logger.info(f"Loading cleaned data from {data_parquet_path}...")
    df = pd.read_parquet(data_parquet_path)
    logger.info(f"Loaded {len(df):,} total records")

    # Filter to top domains to ensure robust, well-represented classes
    df_filtered = df[df["field_of_invention"].isin(config.TOP_DOMAINS)].copy()
    logger.info(f"Filtered to top {len(config.TOP_DOMAINS)} technology domains: {len(df_filtered):,} patents retained")

    if sample_limit and sample_limit < len(df_filtered):
        # Stratified subsampling if user wants rapid experimentation
        df_filtered, _ = train_test_split(
            df_filtered,
            train_size=sample_limit,
            stratify=df_filtered["field_of_invention"],
            random_state=config.RANDOM_SEED
        )
        logger.info(f"Subsampled {len(df_filtered):,} records for fast experimentation")

    # Stratified Train (70%) / Temp (30%) split
    train_df, temp_df = train_test_split(
        df_filtered,
        test_size=(config.TEST_SPLIT_SIZE + config.VAL_SPLIT_SIZE),
        stratify=df_filtered["field_of_invention"],
        random_state=config.RANDOM_SEED
    )

    # Split Temp 50/50 into Validation (15%) and Test (15%)
    val_ratio_of_temp = config.VAL_SPLIT_SIZE / (config.TEST_SPLIT_SIZE + config.VAL_SPLIT_SIZE)
    val_df, test_df = train_test_split(
        temp_df,
        test_size=(1.0 - val_ratio_of_temp),
        stratify=temp_df["field_of_invention"],
        random_state=config.RANDOM_SEED
    )

    logger.info(f"Dataset split completed:")
    logger.info(f"  Train set:      {len(train_df):,} rows ({len(train_df)/len(df_filtered):.1%})")
    logger.info(f"  Validation set: {len(val_df):,} rows ({len(val_df)/len(df_filtered):.1%})")
    logger.info(f"  Test set:       {len(test_df):,} rows ({len(test_df)/len(df_filtered):.1%})")

    # Persist splits
    train_df.to_parquet(config.TRAIN_DATA_PARQUET, index=False)
    val_df.to_parquet(config.VAL_DATA_PARQUET, index=False)
    test_df.to_parquet(config.TEST_DATA_PARQUET, index=False)
    logger.info("Persisted train, val, and test splits to parquet files")

    # 1. Fit LabelEncoder on target
    label_encoder = LabelEncoder()
    train_labels = label_encoder.fit_transform(train_df["field_of_invention"])
    val_labels = label_encoder.transform(val_df["field_of_invention"])
    test_labels = label_encoder.transform(test_df["field_of_invention"])

    joblib.dump(label_encoder, config.LABEL_ENCODER_PATH)
    logger.info(f"Fitted LabelEncoder on {len(label_encoder.classes_)} classes; saved to {config.LABEL_ENCODER_PATH}")

    # 2. Fit TF-IDF Vectorizer on text
    logger.info(f"Fitting TF-IDF Vectorizer (max_features={config.TFIDF_MAX_FEATURES}, ngrams={config.TFIDF_NGRAM_RANGE})...")
    tfidf_vectorizer = TfidfVectorizer(
        ngram_range=config.TFIDF_NGRAM_RANGE,
        max_features=config.TFIDF_MAX_FEATURES,
        sublinear_tf=True,
        stop_words="english",
        min_df=2
    )

    X_train_tfidf = tfidf_vectorizer.fit_transform(train_df[config.TEXT_COLUMN])
    X_val_tfidf = tfidf_vectorizer.transform(val_df[config.TEXT_COLUMN])
    X_test_tfidf = tfidf_vectorizer.transform(test_df[config.TEXT_COLUMN])

    joblib.dump(tfidf_vectorizer, config.TFIDF_VECTORIZER_PATH)
    logger.info(f"Saved TF-IDF vectorizer to {config.TFIDF_VECTORIZER_PATH}")

    # 3. Tabular metadata scaling for regression / hybrid features
    # Filter valid pendency rows (non-null pendency_days)
    reg_train = train_df.dropna(subset=["pendency_days"]).copy()
    reg_val = val_df.dropna(subset=["pendency_days"]).copy()
    reg_test = test_df.dropna(subset=["pendency_days"]).copy()

    meta_cols = ["no_of_pages_imputed", "no_of_claims_imputed"]
    scaler = StandardScaler()
    scaler.fit(reg_train[meta_cols])

    return {
        "train_df": train_df,
        "val_df": val_df,
        "test_df": test_df,
        "X_train_tfidf": X_train_tfidf,
        "X_val_tfidf": X_val_tfidf,
        "X_test_tfidf": X_test_tfidf,
        "y_train": train_labels,
        "y_val": val_labels,
        "y_test": test_labels,
        "label_encoder": label_encoder,
        "tfidf_vectorizer": tfidf_vectorizer,
        "classes": list(label_encoder.classes_)
    }


if __name__ == "__main__":
    split_info = prepare_features_and_splits()
    print("Feature engineering and data partitioning complete!")
    print("Classes:", split_info["classes"])
