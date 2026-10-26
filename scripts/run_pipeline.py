#!/usr/bin/env python3
"""
PatentGraph AI - Complete Data Engineering Pipeline Runner
Autonomous orchestrator for auditing, cleaning, knowledge graph export, RAG preparation, and validation.
Usage:
  python scripts/run_pipeline.py                 # Full end-to-end execution
  python scripts/run_pipeline.py --audit-only   # Read-only audit
  python scripts/run_pipeline.py --skip-graph   # Clean and prepare RAG only
  python scripts/run_pipeline.py --skip-rag     # Clean and prepare Graph only
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("PatentPipeline")

# Import pipeline modules
from audit_datasets import audit_corpus
from clean_datasets import run_cleaning_pipeline
from prepare_graph_data import prepare_knowledge_graph
from prepare_rag_data import build_rag_corpus
from validate_outputs import run_validation


def main():
    parser = argparse.ArgumentParser(description="PatentGraph AI End-to-End Data Pipeline.")
    parser.add_argument("--dataset-dir", default="dataset", help="Path to raw InPASS CSV dataset directory")
    parser.add_argument("--cleaned-dir", default="cleaned", help="Path to cleaned output directory")
    parser.add_argument("--reports-dir", default="reports", help="Path to reports output directory")
    parser.add_argument("--audit-only", action="store_true", help="Run read-only audit without modifications")
    parser.add_argument("--skip-graph", action="store_true", help="Skip Knowledge Graph export")
    parser.add_argument("--skip-rag", action="store_true", help="Skip RAG chunk and document export")
    parser.add_argument("--min-concept-freq", type=int, default=5, help="Concept threshold for graph")
    args = parser.parse_args()

    # Path normalization for execution from root or miniproject/
    base_dir = Path.cwd()
    d_dir = args.dataset_dir
    c_dir = args.cleaned_dir
    r_dir = args.reports_dir

    if not os.path.exists(d_dir) and os.path.exists(os.path.join("miniproject", d_dir)):
        d_dir = os.path.join("miniproject", d_dir)
        c_dir = os.path.join("miniproject", c_dir)
        r_dir = os.path.join("miniproject", r_dir)

    start_time = datetime.now()
    logger.info("=" * 70)
    logger.info("PATENTGRAPH AI: AUTONOMOUS DATA PREPARATION PIPELINE")
    logger.info(f"Start Time: {start_time.isoformat()}")
    logger.info(f"Raw Dataset Dir : {d_dir}")
    logger.info(f"Cleaned Out Dir : {c_dir}")
    logger.info(f"Reports Out Dir : {r_dir}")
    logger.info("=" * 70)

    # STEP 1: AUDIT
    logger.info("\n>>> STEP 1: READ-ONLY DATASET AUDIT & INVENTORY")
    audit_rep = audit_corpus(dataset_dir=d_dir, reports_dir=r_dir)
    logger.info(f"Audit completed: {audit_rep['total_raw_rows']:,} raw records audited.")

    if args.audit_only:
        logger.info("\nAudit-only flag specified. Pipeline execution halted as requested.")
        return

    # STEP 2: CLEANING & STANDARDIZATION
    logger.info("\n>>> STEP 2: DATA CLEANING & STANDARDIZATION")
    clean_res = run_cleaning_pipeline(
        dataset_dir=d_dir,
        cleaned_dir=c_dir,
        reports_dir=r_dir,
        sync_to_backend=True,
        sync_to_ml_pipeline=True
    )
    logger.info(f"Cleaning completed: {clean_res['total_valid_records']:,} valid, {clean_res['total_quarantined_records']} quarantined.")

    # STEP 3: KNOWLEDGE GRAPH PREPARATION
    if not args.skip_graph:
        logger.info("\n>>> STEP 3: KNOWLEDGE GRAPH DATA GENERATION")
        graph_out = os.path.join(c_dir, "graph")
        parquet_file = os.path.join(c_dir, "cleaned_patents_consolidated.parquet")
        graph_res = prepare_knowledge_graph(
            cleaned_data_path=parquet_file,
            graph_output_dir=graph_out,
            reports_dir=r_dir,
            min_concept_frequency=args.min_concept_freq
        )
        logger.info(f"Graph preparation completed: {graph_res['total_nodes']:,} nodes, {graph_res['total_edges']:,} edges.")
    else:
        logger.info("\n>>> STEP 3: KNOWLEDGE GRAPH GENERATION SKIPPED (--skip-graph)")

    # STEP 4: RAG RETRIEVAL PREPARATION
    if not args.skip_rag:
        logger.info("\n>>> STEP 4: RAG DOCUMENTS & CHUNK GENERATION")
        rag_out = os.path.join(c_dir, "rag")
        parquet_file = os.path.join(c_dir, "cleaned_patents_consolidated.parquet")
        rag_res = build_rag_corpus(
            cleaned_parquet_path=parquet_file,
            output_rag_dir=rag_out,
            reports_dir=r_dir
        )
        logger.info(f"RAG preparation completed: {rag_res['total_documents']:,} docs, {rag_res['total_chunks']:,} chunks.")
    else:
        logger.info("\n>>> STEP 4: RAG GENERATION SKIPPED (--skip-rag)")

    # STEP 5: AUTOMATED VALIDATION
    logger.info("\n>>> STEP 5: AUTOMATED OUTPUT VALIDATION SUITE")
    val_res = run_validation(
        dataset_dir=d_dir,
        cleaned_dir=c_dir,
        reports_dir=r_dir
    )

    elapsed = datetime.now() - start_time
    logger.info("=" * 70)
    logger.info(f"PIPELINE EXECUTION COMPLETE in {elapsed.total_seconds():.1f} seconds.")
    logger.info(f"Validation Status: {val_res['status']}")
    logger.info("=" * 70)

    if val_res["status"] != "PASSED":
        logger.error("Pipeline finished with validation failures.")
        sys.exit(1)


if __name__ == "__main__":
    main()
