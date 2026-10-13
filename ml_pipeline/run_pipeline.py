"""Master End-to-End Pipeline Runner.
Orchestrates data ingestion, cleaning, feature engineering, classification,
deep learning, regression, clustering, and visualization in a single workflow.
"""

import os
os.environ["USE_TF"] = "0"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import sys
import time
import argparse
import logging

# Ensure ml_pipeline is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import config
from src.data_cleaning import clean_and_preprocess_dataset
from src.feature_engineering import prepare_features_and_splits
from src.train_classifier import train_and_evaluate_classifiers
from src.train_neural import train_neural_network
from src.train_regressor import train_pendency_regressor
from src.train_clustering import train_patent_clustering
from src.evaluate import generate_evaluation_artifacts

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run_full_pipeline(sample_limit: int = None, skip_cleaning: bool = False, skip_neural: bool = False):
    """Run all stages of the Patent ML Pipeline."""
    total_start = time.time()
    logger.info("=" * 65)
    logger.info("STARTING PATENT DATA CLEANING & MACHINE LEARNING PIPELINE")
    logger.info("=" * 65)

    # Stage 1: Data Cleaning & Ingestion
    if not skip_cleaning or not config.CLEANED_DATA_PARQUET.exists():
        logger.info("\n>>> [STAGE 1/7] Data Cleaning and Preprocessing...")
        clean_and_preprocess_dataset()
    else:
        logger.info("\n>>> [STAGE 1/7] Cleaned data already exists. Skipping raw ingestion.")

    # Stage 2: Feature Engineering & Train/Val/Test Split
    logger.info("\n>>> [STAGE 2/7] Feature Engineering & Train/Val/Test Partitioning...")
    feature_data = prepare_features_and_splits(sample_limit=sample_limit)

    # Stage 3: Multi-Class NLP Classification Training
    logger.info("\n>>> [STAGE 3/7] Training & Benchmarking NLP Classifiers...")
    cls_results = train_and_evaluate_classifiers(feature_data)

    # Stage 4: PyTorch Neural Network Classifier
    if not skip_neural:
        logger.info("\n>>> [STAGE 4/7] Training PyTorch Deep Text Classifier...")
        try:
            train_neural_network(feature_data, epochs=config.NEURAL_EPOCHS)
        except Exception as e:
            logger.error(f"PyTorch training encountered an issue: {e}. Continuing with remaining pipeline...")
    else:
        logger.info("\n>>> [STAGE 4/7] Skipping Neural Network as requested.")

    # Stage 5: Patent Examination Pendency Regression
    logger.info("\n>>> [STAGE 5/7] Training Patent Prosecution Pendency Regressor...")
    train_pendency_regressor(feature_data)

    # Stage 6: Unsupervised Clustering & Topic Discovery
    logger.info("\n>>> [STAGE 6/7] Running Unsupervised Latent Technology Clustering...")
    train_patent_clustering(feature_data)

    # Stage 7: Evaluation Benchmark & Visual Plots
    logger.info("\n>>> [STAGE 7/7] Generating Comprehensive Benchmark Reports & Plots...")
    benchmark_df = generate_evaluation_artifacts()

    elapsed = time.time() - total_start
    logger.info("\n" + "=" * 65)
    logger.info(f"ML PIPELINE COMPLETED SUCCESSFULLY IN {elapsed:.1f} SECONDS!")
    logger.info("=" * 65)

    if not benchmark_df.empty:
        print("\n=== FINAL BENCHMARK SUMMARY TABLE ===")
        print(benchmark_df.to_string(index=False))
        print("\nSaved artifacts:")
        print(f"  - Cleaned Dataset:     {config.CLEANED_DATA_PARQUET}")
        print(f"  - Model Weights:       {config.MODELS_DIR}")
        print(f"  - Reports & Visuals:   {config.REPORTS_DIR}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Patent ML Pipeline")
    parser.add_argument("--sample_limit", type=int, default=None, help="Optional limit for rapid testing (e.g. 20000)")
    parser.add_argument("--skip_cleaning", action="store_true", help="Skip data cleaning if cleaned parquet exists")
    parser.add_argument("--skip_neural", action="store_true", help="Skip PyTorch deep learning training")
    args = parser.parse_args()

    run_full_pipeline(
        sample_limit=args.sample_limit,
        skip_cleaning=args.skip_cleaning,
        skip_neural=args.skip_neural
    )
