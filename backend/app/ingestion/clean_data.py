import os
import re
import glob
import json
import logging
from datetime import datetime
from typing import Dict, Any, Tuple, List
import pandas as pd
import numpy as np

from typing import Dict, Any, Tuple, List, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

RAW_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "..", "dataset")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

def clean_title_text(text: Any) -> str:
    """Clean patent title: strip quotation marks, corrupt encoding markers, normalize spaces."""
    if pd.isna(text) or text is None:
        return ""
    text_str = str(text)
    # Remove corrupt replacement chars or special quotes
    text_str = text_str.replace('\ufffd', '').replace('"', '').replace('"', '').replace('"', '').replace("'", "").replace("'", "")
    text_str = text_str.strip('"\';:,.- ')
    # Normalize consecutive whitespace
    text_str = re.sub(r'\s+', ' ', text_str).strip()
    return text_str

def parse_inpass_date(date_str: Any) -> Optional[str]:
    """Parse InPASS date format (DD/MM/YYYY) into ISO standard (YYYY-MM-DD)."""
    if pd.isna(date_str) or not date_str:
        return None
    d = str(date_str).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(d, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None

def normalize_field(field_val: Any) -> str:
    """Normalize field of invention string."""
    if pd.isna(field_val) or not field_val:
        return "GENERAL / UNCATEGORIZED"
    cleaned = str(field_val).strip().upper()
    return cleaned if cleaned else "GENERAL / UNCATEGORIZED"

def run_preprocessing(dataset_dir: str = RAW_DATA_DIR, output_dir: str = OUTPUT_DIR) -> Dict[str, Any]:
    """Ingest, clean, validate, and persist all Indian patent records."""
    os.makedirs(output_dir, exist_ok=True)
    csv_paths = sorted(glob.glob(os.path.join(dataset_dir, "*.csv")))
    
    if not csv_paths:
        raise FileNotFoundError(f"No CSV files found in dataset directory: {dataset_dir}")
        
    logger.info(f"Discovered {len(csv_paths)} CSV files in {dataset_dir}")
    
    dfs = []
    file_stats = {}
    
    for path in csv_paths:
        fname = os.path.basename(path)
        df_part = pd.read_csv(path, low_memory=False, dtype=str)
        initial_count = len(df_part)
        file_stats[fname] = initial_count
        logger.info(f"Loaded {fname}: {initial_count:,} raw rows")
        dfs.append(df_part)
        
    combined = pd.concat(dfs, ignore_index=True)
    total_raw_records = len(combined)
    logger.info(f"Total concatenated raw records: {total_raw_records:,}")

    # Check and remove exact duplicates
    exact_duplicates = int(combined.duplicated().sum())
    if exact_duplicates > 0:
        combined = combined.drop_duplicates()
        logger.warning(f"Removed {exact_duplicates:,} exact duplicate rows")

    # Clean and map schema
    records_to_validate = []
    invalid_records = []
    
    for idx, row in combined.iterrows():
        app_num = str(row.get("APPLICATION_NUMBER", "")).strip()
        pub_num = str(row.get("PUBLICATION_NUMBER", "")).strip() if pd.notna(row.get("PUBLICATION_NUMBER")) else None
        raw_title = row.get("TITLE_OF_INVENTION")
        cleaned_title = clean_title_text(raw_title)
        
        # Validation rule: must have a non-empty patent id and title
        if not app_num or not cleaned_title:
            invalid_records.append({
                "row_index": int(idx),
                "application_number": app_num,
                "raw_title": str(raw_title),
                "reason": "Missing required APPLICATION_NUMBER or TITLE_OF_INVENTION"
            })
            continue

        raw_filing = row.get("DATE_OF_FILING")
        filing_iso = parse_inpass_date(raw_filing)

        raw_pub = row.get("PUBLICATION_DATE")
        pub_iso = parse_inpass_date(raw_pub)

        raw_field = row.get("FIELD_OF_INVENTION")
        field_norm = normalize_field(raw_field)

        ipo_loc = str(row.get("IPO_LOCATION", "")).strip().title() if pd.notna(row.get("IPO_LOCATION")) else "India"
        app_type = str(row.get("APPLICATION_TYPE_DESC", "")).strip() if pd.notna(row.get("APPLICATION_TYPE_DESC")) else None
        
        # Claims and pages count
        try:
            claims = int(float(row.get("NO_OF_CLAIMS"))) if pd.notna(row.get("NO_OF_CLAIMS")) else None
        except (ValueError, TypeError):
            claims = None

        try:
            pages = int(float(row.get("NO_OF_PAGES"))) if pd.notna(row.get("NO_OF_PAGES")) else None
        except (ValueError, TypeError):
            pages = None

        source_url = f"https://ipindiaservices.gov.in/publicsearch/"

        # Synthesize technical search representation combining title, field, and type
        search_repr = f"{cleaned_title}. Technical Field: {field_norm}. Patent Office: {ipo_loc}. Type: {app_type or 'Patent'}."

        records_to_validate.append({
            "patent_id": app_num,
            "publication_number": pub_num,
            "title": cleaned_title,
            "field_of_invention": field_norm,
            "ipo_location": ipo_loc,
            "application_type": app_type,
            "filing_date": filing_iso,
            "publication_date": pub_iso,
            "no_of_claims": claims,
            "no_of_pages": pages,
            "jurisdiction": "India",
            "source_url": source_url,
            "search_text": search_repr,
            "status": "Granted"
        })

    cleaned_df = pd.DataFrame(records_to_validate)
    
    # Deduplicate on patent_id (APPLICATION_NUMBER) if any
    dup_ids = int(cleaned_df.duplicated(subset=["patent_id"]).sum())
    if dup_ids > 0:
        cleaned_df = cleaned_df.drop_duplicates(subset=["patent_id"], keep="first")
        logger.warning(f"Deduplicated {dup_ids} duplicate patent IDs")

    total_valid = len(cleaned_df)
    total_invalid = len(invalid_records)
    logger.info(f"Cleaned dataset: {total_valid:,} valid patents | {total_invalid} invalid records")

    # Persist in Parquet and JSONL
    parquet_path = os.path.join(output_dir, "cleaned_patents.parquet")
    jsonl_path = os.path.join(output_dir, "cleaned_patents.jsonl")
    cleaned_df.to_parquet(parquet_path, index=False)
    logger.info(f"Saved Parquet file: {parquet_path}")

    # Generate Validation Report
    report = {
        "execution_timestamp": datetime.now().isoformat(),
        "total_raw_rows_loaded": total_raw_records,
        "files_processed": file_stats,
        "exact_duplicates_removed": exact_duplicates,
        "duplicate_patent_ids_resolved": dup_ids,
        "total_valid_patents": total_valid,
        "total_invalid_patents": total_invalid,
        "field_distribution": cleaned_df["field_of_invention"].value_counts().to_dict(),
        "ipo_location_distribution": cleaned_df["ipo_location"].value_counts().to_dict(),
        "date_coverage": {
            "earliest_filing_date": str(cleaned_df["filing_date"].min()),
            "latest_filing_date": str(cleaned_df["filing_date"].max()),
            "earliest_publication_date": str(cleaned_df["publication_date"].min()),
            "latest_publication_date": str(cleaned_df["publication_date"].max())
        },
        "missing_attributes": {
            "missing_filing_date": int(cleaned_df["filing_date"].isna().sum()),
            "missing_publication_date": int(cleaned_df["publication_date"].isna().sum()),
            "missing_claims_count": int(cleaned_df["no_of_claims"].isna().sum()),
            "missing_pages_count": int(cleaned_df["no_of_pages"].isna().sum())
        }
    }

    report_path = os.path.join(output_dir, "preprocessing_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Saved Preprocessing Report: {report_path}")

    if invalid_records:
        invalid_path = os.path.join(output_dir, "invalid_records_report.json")
        with open(invalid_path, "w", encoding="utf-8") as f:
            json.dump(invalid_records, f, indent=2)
        logger.info(f"Saved Invalid Records Report: {invalid_path}")

    return report

if __name__ == "__main__":
    rep = run_preprocessing()
    print("Preprocessing completed successfully!")
    print(json.dumps(rep, indent=2))
