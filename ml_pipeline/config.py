"""Configuration file for Patent ML Pipeline.
Defines directories, filepaths, hyperparameters, and feature settings.
"""

import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

RAW_DATA_DIR = PROJECT_ROOT / "dataset"
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
REPORTS_DIR = BASE_DIR / "reports"
SRC_DIR = BASE_DIR / "src"

# Ensure runtime directories exist
for directory in [DATA_DIR, MODELS_DIR, REPORTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Processed Data Paths
CLEANED_DATA_PARQUET = DATA_DIR / "cleaned_patents.parquet"
CLEANED_DATA_CSV = DATA_DIR / "cleaned_patents_sample.csv"
TRAIN_DATA_PARQUET = DATA_DIR / "train_split.parquet"
VAL_DATA_PARQUET = DATA_DIR / "val_split.parquet"
TEST_DATA_PARQUET = DATA_DIR / "test_split.parquet"
PREPROCESSING_SUMMARY_JSON = DATA_DIR / "preprocessing_summary.json"

# Model Paths
TFIDF_VECTORIZER_PATH = MODELS_DIR / "tfidf_vectorizer.joblib"
LABEL_ENCODER_PATH = MODELS_DIR / "label_encoder.joblib"
BEST_CLASSIFIER_PATH = MODELS_DIR / "best_domain_classifier.joblib"
ALL_CLASSIFIERS_PATH = MODELS_DIR / "all_classifiers.joblib"
NEURAL_CLASSIFIER_PATH = MODELS_DIR / "neural_classifier.pt"
PENDENCY_REGRESSOR_PATH = MODELS_DIR / "pendency_regressor.joblib"
KMEANS_MODEL_PATH = MODELS_DIR / "kmeans_clustering.joblib"

# Reports Paths
CLASSIFICATION_METRICS_JSON = REPORTS_DIR / "classification_metrics.json"
REGRESSION_METRICS_JSON = REPORTS_DIR / "regression_metrics.json"
CLUSTERING_SUMMARY_JSON = REPORTS_DIR / "clustering_summary.json"
BENCHMARK_SUMMARY_CSV = REPORTS_DIR / "benchmark_summary.csv"
CONFUSION_MATRIX_PNG = REPORTS_DIR / "confusion_matrix.png"
MODEL_COMPARISON_PNG = REPORTS_DIR / "model_comparison.png"

# Target & Feature Settings
TARGET_COLUMN = "field_of_invention"
TEXT_COLUMN = "title_clean"
METADATA_COLUMNS = ["ipo_location", "application_type", "filing_year"]

# Top technology domains to include in multi-class classification
TOP_DOMAINS = [
    "CHEMISTRY",
    "MECHANICAL",
    "ELECTRONICS",
    "ELECTRICAL",
    "COMMUNICATION",
    "POLYMER",
    "COMPUTER",
    "PHYSICS",
    "BIOTECHNOLOGY",
    "BIOMEDICAL",
    "METALLURGY",
    "TEXTILE",
    "BIOCHEMISTRY",
    "CIVIL",
    "FOOD"
]

# Hyperparameters
RANDOM_SEED = 42
TEST_SPLIT_SIZE = 0.15
VAL_SPLIT_SIZE = 0.15
TFIDF_MAX_FEATURES = 15000
TFIDF_NGRAM_RANGE = (1, 2)
KMEANS_CLUSTERS = 10

# Neural Network Hyperparameters
NEURAL_EMBED_DIM = 128
NEURAL_HIDDEN_DIM = 256
NEURAL_DROPOUT = 0.3
NEURAL_BATCH_SIZE = 64
NEURAL_EPOCHS = 8
NEURAL_LR = 0.002
