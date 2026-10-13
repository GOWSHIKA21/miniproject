"""Data Cleaning and Ingestion Module.
Ingests raw Indian Patent Office CSVs, performs rigorous text normalization,
date parsing, feature derivation, deduplication, and persists clean datasets.
"""

import os
import re
import glob
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def clean_text(text: Any) -> str:
    """Clean patent title: remove corrupt characters, quotes, extra whitespace."""
    if pd.isna(text) or text is None:
        return ""
    text_str = str(text)
    # Remove corrupt characters and quote marks
    text_str = text_str.replace('\ufffd', ' ').replace('"', '').replace('"', '').replace('"', '')
    text_str = text_str.replace("'", "").replace("'", "")
    # Remove non-ascii noise while preserving alphanumeric and punctuation
    text_str = re.sub(r'[^\x00-\x7F]+', ' ', text_str)
    # Normalize multiple whitespace
    text_str = re.sub(r'\s+', ' ', text_str).strip()
    return text_str


def parse_date(date_val: Any) -> Optional[datetime]:
    """Parse Indian Patent date format into standard datetime."""
    if pd.isna(date_val) or not date_val:
        return None
    d_str = str(date_val).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(d_str, fmt)
        except ValueError:
            pass
    return None


def normalize_field(field_val: Any) -> str:
    """Normalize field of invention."""
    if pd.isna(field_val) or not field_val:
        return "OTHER"
    cleaned = str(field_val).strip().upper()
    return cleaned if cleaned else "OTHER"


def clean_and_preprocess_dataset(
    raw_data_dir: str = str(config.RAW_DATA_DIR),
    output_parquet: str = str(config.CLEANED_DATA_PARQUET),
    output_sample_csv: str = str(config.CLEANED_DATA_CSV),
    sync_to_backend: bool = True
) -> pd.DataFrame:
    """Execute complete cleaning and feature preprocessing pipeline."""
    csv_files = sorted(glob.glob(os.path.join(raw_data_dir, "*.csv")))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {raw_data_dir}")

    logger.info(f"Discovered {len(csv_files)} CSV files in {raw_data_dir}")

    dfs = []
    file_records = {}

    for fpath in csv_files:
        fname = os.path.basename(fpath)
        df_part = pd.read_csv(fpath, low_memory=False, dtype=str)
        count = len(df_part)
        file_records[fname] = count
        logger.info(f"Loaded {fname}: {count:,} rows")
        dfs.append(df_part)

    df_raw = pd.concat(dfs, ignore_index=True)
    total_raw = len(df_raw)
    logger.info(f"Total raw records loaded: {total_raw:,}")

    # Remove exact duplicate rows
    initial_dups = int(df_raw.duplicated().sum())
    if initial_dups > 0:
        df_raw = df_raw.drop_duplicates()
        logger.info(f"Dropped {initial_dups:,} exact duplicate rows")

    cleaned_records = []
    dropped_invalid = 0

    for idx, row in df_raw.iterrows():
        app_num = str(row.get("APPLICATION_NUMBER", "")).strip()
        raw_title = row.get("TITLE_OF_INVENTION")
        title_cleaned = clean_text(raw_title)

        # Validation: must have non-empty ID and title with at least 3 characters
        if not app_num or len(title_cleaned) < 3 or app_num.lower() == "nan":
            dropped_invalid += 1
            continue

        pub_num = str(row.get("PUBLICATION_NUMBER", "")).strip() if pd.notna(row.get("PUBLICATION_NUMBER")) else None
        field_norm = normalize_field(row.get("FIELD_OF_INVENTION"))
        ipo_loc = str(row.get("IPO_LOCATION", "India")).strip().title() if pd.notna(row.get("IPO_LOCATION")) else "India"
        app_type = str(row.get("APPLICATION_TYPE_DESC", "Patent")).strip() if pd.notna(row.get("APPLICATION_TYPE_DESC")) else "Patent"

        # Dates and pendency calculation
        filing_dt = parse_date(row.get("DATE_OF_FILING"))
        pub_dt = parse_date(row.get("PUBLICATION_DATE"))

        filing_iso = filing_dt.strftime("%Y-%m-%d") if filing_dt else None
        pub_iso = pub_dt.strftime("%Y-%m-%d") if pub_dt else None
        filing_year = filing_dt.year if filing_dt else None
        pub_year = pub_dt.year if pub_dt else None

        pendency_days = None
        if filing_dt and pub_dt:
            diff = (pub_dt - filing_dt).days
            # Filter unrealistic pendency (between 0 and 30 years)
            if 0 <= diff <= 10950:
                pendency_days = diff

        # Numerical fields
        try:
            pages = int(float(row.get("NO_OF_PAGES"))) if pd.notna(row.get("NO_OF_PAGES")) else None
            if pages is not None and (pages < 1 or pages > 1000):
                pages = None
        except (ValueError, TypeError):
            pages = None

        try:
            claims = int(float(row.get("NO_OF_CLAIMS"))) if pd.notna(row.get("NO_OF_CLAIMS")) else None
            if claims is not None and (claims < 1 or claims > 500):
                claims = None
        except (ValueError, TypeError):
            claims = None

        # Enriched combined text for NLP & semantic modeling
        enriched_text = f"{title_cleaned}. Field: {field_norm}. Jurisdiction: {ipo_loc}."

        cleaned_records.append({
            "patent_id": app_num,
            "publication_number": pub_num,
            "title": title_cleaned,
            "title_clean": title_cleaned.lower(),
            "field_of_invention": field_norm,
            "ipo_location": ipo_loc,
            "application_type": app_type,
            "filing_date": filing_iso,
            "publication_date": pub_iso,
            "filing_year": filing_year,
            "publication_year": pub_year,
            "pendency_days": pendency_days,
            "no_of_pages": pages,
            "no_of_claims": claims,
            "search_text": enriched_text,
            "source_url": "https://ipindiaservices.gov.in/publicsearch/"
        })

    cleaned_df = pd.DataFrame(cleaned_records)

    # Deduplicate on patent_id keeping first occurrence
    id_dups = int(cleaned_df.duplicated(subset=["patent_id"]).sum())
    if id_dups > 0:
        cleaned_df = cleaned_df.drop_duplicates(subset=["patent_id"], keep="first")
        logger.info(f"Resolved {id_dups:,} duplicate patent IDs")

    # Impute missing numericals with median for ML pipeline readiness
    median_pages = cleaned_df["no_of_pages"].median()
    median_claims = cleaned_df["no_of_claims"].median()
    cleaned_df["no_of_pages_imputed"] = cleaned_df["no_of_pages"].fillna(median_pages)
    cleaned_df["no_of_claims_imputed"] = cleaned_df["no_of_claims"].fillna(median_claims)

    total_valid = len(cleaned_df)
    logger.info(f"Cleaning complete: {total_valid:,} valid patents retained ({dropped_invalid} discarded)")

    # Save to Parquet
    cleaned_df.to_parquet(output_parquet, index=False)
    logger.info(f"Saved cleaned parquet dataset: {output_parquet}")

    # Save small CSV sample (5,000 rows) for easy manual examination
    sample_size = min(5000, total_valid)
    cleaned_df.head(sample_size).to_csv(output_sample_csv, index=False)
    logger.info(f"Saved {sample_size} sample records to CSV: {output_sample_csv}")

    # Optionally copy to backend data folder
    if sync_to_backend:
        backend_data_dir = config.PROJECT_ROOT / "backend" / "app" / "data"
        backend_data_dir.mkdir(parents=True, exist_ok=True)
        backend_parquet = backend_data_dir / "cleaned_patents.parquet"
        cleaned_df.to_parquet(backend_parquet, index=False)
        logger.info(f"Synchronized cleaned parquet to backend: {backend_parquet}")

    # Save Preprocessing Summary Report
    summary = {
        "execution_time": datetime.now().isoformat(),
        "total_raw_rows": total_raw,
        "files_processed": file_records,
        "exact_duplicates_removed": initial_dups,
        "invalid_rows_discarded": dropped_invalid,
        "id_duplicates_resolved": id_dups,
        "total_valid_cleaned_records": total_valid,
        "field_counts": cleaned_df["field_of_invention"].value_counts().head(20).to_dict(),
        "location_counts": cleaned_df["ipo_location"].value_counts().to_dict(),
        "application_type_counts": cleaned_df["application_type"].value_counts().head(10).to_dict(),
        "median_claims": float(median_claims) if pd.notna(median_claims) else 0.0,
        "median_pages": float(median_pages) if pd.notna(median_pages) else 0.0,
        "date_ranges": {
            "earliest_filing": str(cleaned_df["filing_date"].dropna().min()),
            "latest_filing": str(cleaned_df["filing_date"].dropna().max()),
            "earliest_publication": str(cleaned_df["publication_date"].dropna().min()),
            "latest_publication": str(cleaned_df["publication_date"].dropna().max()),
        }
    }

    with open(config.PREPROCESSING_SUMMARY_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Saved preprocessing summary to {config.PREPROCESSING_SUMMARY_JSON}")

    return cleaned_df


if __name__ == "__main__":
    df = clean_and_preprocess_dataset()
    print("Dataset successfully cleaned and preprocessed!")
    print(f"Total patents: {len(df):,}")
