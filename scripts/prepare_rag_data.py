#!/usr/bin/env python3
"""
PatentGraph AI - RAG Data Preparation Script
Prepares retrieval-ready documents and semantic chunks from cleaned patent datasets.
Features:
  - Generates full document representation for high-level retrieval.
  - Generates structured, configurable semantic chunks with stable, unique IDs.
  - Links every chunk back to parent patent_id and source provenance.
  - Detects empty and duplicate chunks.
  - Outputs:
    - cleaned/rag/rag_documents.jsonl
    - cleaned/rag/rag_chunks.jsonl
    - cleaned/rag/rag_chunks.parquet
    - cleaned/rag/rag_metadata_summary.json
    - reports/rag_preparation_report.md
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("RAGPreparer")


def build_rag_corpus(
    cleaned_parquet_path: str = "cleaned/cleaned_patents_consolidated.parquet",
    output_rag_dir: str = "cleaned/rag",
    reports_dir: str = "reports"
) -> Dict[str, Any]:
    """Generate RAG-ready document store and chunk index."""
    cleaned_file = Path(cleaned_parquet_path).resolve()
    out_dir = Path(output_rag_dir).resolve()
    rep_dir = Path(reports_dir).resolve()

    out_dir.mkdir(parents=True, exist_ok=True)
    rep_dir.mkdir(parents=True, exist_ok=True)

    if not cleaned_file.exists():
        raise FileNotFoundError(f"Cleaned dataset not found at {cleaned_file}")

    logger.info(f"Loading cleaned dataset from {cleaned_file}...")
    df = pd.read_parquet(cleaned_file)
    total_records = len(df)
    logger.info(f"Loaded {total_records:,} patent records.")

    documents_jsonl_path = out_dir / "rag_documents.jsonl"
    chunks_jsonl_path = out_dir / "rag_chunks.jsonl"
    chunks_parquet_path = out_dir / "rag_chunks.parquet"

    logger.info("Generating documents and semantic chunks...")

    total_chunks = 0
    all_chunks_list = []
    chunk_id_set = set()
    duplicate_chunks_detected = 0
    empty_chunks_detected = 0

    with open(documents_jsonl_path, "w", encoding="utf-8") as doc_f, \
         open(chunks_jsonl_path, "w", encoding="utf-8") as chunk_f:

        for _, row in df.iterrows():
            p_id = str(row["patent_id"])
            title = str(row["title"])
            field = str(row["field_of_invention"])
            ipo_loc = str(row["ipo_location"])
            ipo_code = str(row["ipo_code"])
            app_type = str(row["application_type"])
            app_cat = str(row["application_category"])
            filing_date = str(row["filing_date"]) if pd.notna(row["filing_date"]) else "Unknown"
            pub_date = str(row["publication_date"]) if pd.notna(row["publication_date"]) else "Unknown"
            pub_num = str(row["publication_number"]) if pd.notna(row["publication_number"]) else "N/A"
            pendency = int(row["pendency_days"]) if pd.notna(row["pendency_days"]) else None
            claims = int(row["no_of_claims"]) if pd.notna(row["no_of_claims"]) else None
            pages = int(row["no_of_pages"]) if pd.notna(row["no_of_pages"]) else None
            claims_range = str(row["claims_range"])
            source_file = str(row["source_file"])
            source_url = str(row["source_url"])

            # 1. Document Representation
            doc_body = (
                f"Patent ID: {p_id}\n"
                f"Title: {title}\n"
                f"Field of Invention: {field}\n"
                f"IPO Office: {ipo_loc} ({ipo_code})\n"
                f"Application Procedure: {app_type} ({app_cat})\n"
                f"Filing Date: {filing_date}\n"
                f"Publication Date: {pub_date} (Gazette Issue: {pub_num})\n"
                f"Turnaround Pendency: {f'{pendency} days' if pendency is not None else 'Unrecorded'}\n"
                f"Scope: {f'{claims} claims' if claims is not None else 'Unspecified claims'}, {f'{pages} pages' if pages is not None else 'Unspecified pages'}\n"
                f"Verification Portal: {source_url}"
            )

            # Define 3 semantic chunks per patent
            c0_id = f"{p_id}#c_invention"
            c0_text = f"Invention: {title}. Technology Domain: {field}. Classification assigned by Indian Patent Office {ipo_loc}."

            c1_id = f"{p_id}#c_procedure"
            c1_text = (
                f"Patent Application {p_id} was filed at IPO {ipo_loc} ({ipo_code}) on {filing_date} as {app_type} ({app_cat}). "
                f"Granted and published in InPASS Gazette under journal issue {pub_num} on {pub_date}"
                f"{f' with a total prosecution pendency of {pendency} days' if pendency is not None else ''}."
            )

            c2_id = f"{p_id}#c_scope"
            c2_text = (
                f"Patent {p_id} specification encompasses {f'{pages} pages' if pages is not None else 'unrecorded page count'} "
                f"and contains {f'{claims} granted claims ({claims_range})' if claims is not None else 'unrecorded claim count'}. "
                f"Official IPO Verification Portal: {source_url}."
            )

            chunk_defs = [
                (c0_id, "invention_overview", c0_text),
                (c1_id, "procedural_history", c1_text),
                (c2_id, "scope_and_claims", c2_text)
            ]

            doc_entry = {
                "patent_id": p_id,
                "publication_number": pub_num,
                "title": title,
                "field_of_invention": field,
                "ipo_location": ipo_loc,
                "ipo_code": ipo_code,
                "application_type": app_type,
                "application_category": app_cat,
                "filing_date": filing_date,
                "publication_date": pub_date,
                "pendency_days": pendency,
                "no_of_claims": claims,
                "no_of_pages": pages,
                "claims_range": claims_range,
                "document_text": doc_body,
                "chunk_ids": [c[0] for c in chunk_defs],
                "source_file": source_file,
                "source_url": source_url
            }
            doc_f.write(json.dumps(doc_entry) + "\n")

            # Write Chunks
            for c_id, section, c_text in chunk_defs:
                # Validate uniqueness
                if c_id in chunk_id_set:
                    duplicate_chunks_detected += 1
                chunk_id_set.add(c_id)

                if not c_text or not c_text.strip():
                    empty_chunks_detected += 1

                chunk_entry = {
                    "chunk_id": c_id,
                    "patent_id": p_id,
                    "section": section,
                    "chunk_text": c_text,
                    "char_count": len(c_text),
                    "word_count": len(c_text.split()),
                    "field_of_invention": field,
                    "ipo_location": ipo_loc,
                    "filing_date": filing_date,
                    "publication_date": pub_date,
                    "source_file": source_file,
                    "source_url": source_url
                }
                chunk_f.write(json.dumps(chunk_entry) + "\n")
                all_chunks_list.append(chunk_entry)
                total_chunks += 1

    logger.info(f"Generated {total_records:,} documents and {total_chunks:,} chunks.")
    logger.info(f"Duplicate chunks: {duplicate_chunks_detected} | Empty chunks: {empty_chunks_detected}")

    # Persist Chunks in Parquet for high-speed columnar retrieval
    logger.info("Persisting chunks to Parquet format...")
    df_chunks = pd.DataFrame(all_chunks_list)
    df_chunks.to_parquet(chunks_parquet_path, index=False)
    logger.info(f"Saved chunks Parquet: {chunks_parquet_path} ({os.path.getsize(chunks_parquet_path):,} bytes)")

    # Compute Statistics
    avg_words = float(df_chunks["word_count"].mean())
    max_words = int(df_chunks["word_count"].max())
    min_words = int(df_chunks["word_count"].min())
    section_counts = df_chunks["section"].value_counts().to_dict()

    summary = {
        "generated_timestamp": datetime.now().isoformat(),
        "total_documents": total_records,
        "total_chunks": total_chunks,
        "duplicate_chunks": duplicate_chunks_detected,
        "empty_chunks": empty_chunks_detected,
        "unique_chunk_ids": len(chunk_id_set),
        "chunk_length_statistics": {
            "average_words_per_chunk": round(avg_words, 2),
            "min_words": min_words,
            "max_words": max_words
        },
        "section_breakdown": section_counts,
        "file_artifacts": {
            "documents_jsonl": str(documents_jsonl_path),
            "chunks_jsonl": str(chunks_jsonl_path),
            "chunks_parquet": str(chunks_parquet_path)
        }
    }

    with open(out_dir / "rag_metadata_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Markdown Report
    rep_lines = [
        "# PatentGraph AI — RAG Retrieval Corpus Preparation Report",
        "",
        f"**Generated**: `{summary['generated_timestamp']}`  ",
        f"**RAG Storage Directory**: `{out_dir}`  ",
        f"**Total Patent Documents**: `{total_records:,}`  ",
        f"**Total Semantic Chunks**: `{total_chunks:,}`  ",
        f"**Unique Chunk Identifiers**: `{len(chunk_id_set):,}`  ",
        f"**Duplicate Chunks**: `{duplicate_chunks_detected}`  ",
        f"**Empty Chunks**: `{empty_chunks_detected}`  ",
        "",
        "---",
        "",
        "## 1. Chunk Length & Word Count Distributions",
        "",
        f"- **Average Words per Chunk**: `{summary['chunk_length_statistics']['average_words_per_chunk']}` words  ",
        f"- **Minimum Words**: `{summary['chunk_length_statistics']['min_words']}` words  ",
        f"- **Maximum Words**: `{summary['chunk_length_statistics']['max_words']}` words  ",
        "",
        "| Semantic Section | Chunk Count | Purpose in Retrieval |",
        "| :--- | :---: | :--- |"
    ]
    for sec, count in section_counts.items():
        purpose = {
            "invention_overview": "Semantic matching on technological claims and invention concepts",
            "procedural_history": "Filtering and QA over IPO office jurisdiction, filing/grant timeline, and legal procedure",
            "scope_and_claims": "Quantitative queries on claims scope, specification length, and IPO gazette verification"
        }.get(sec, "General retrieval context")
        rep_lines.append(f"| `{sec}` | {count:,} | {purpose} |")

    rep_lines.extend([
        "",
        "---",
        "",
        "## 2. Chunk Identification & Schema",
        "Every chunk follows the canonical schema:",
        "- `chunk_id`: Deterministic composite `{patent_id}#{section_slug}` (e.g. `10/DEL/2010#c_invention`).",
        "- `patent_id`: Foreign key link to canonical patent entity.",
        "- `section`: Segment taxonomy indicator.",
        "- `chunk_text`: Natural language text chunk.",
        "- `char_count` & `word_count`: Exact length metrics.",
        "- `field_of_invention`, `ipo_location`, `filing_date`, `publication_date`: Retained metadata for pre/post-retrieval filtering.",
        "- `source_file` & `source_url`: Full provenance and official IPO gazette ground-truth evidence link.",
        "",
        "---",
        "",
        "## 3. Storage Formats Prepared",
        f"1. **`rag_documents.jsonl`** ({os.path.getsize(documents_jsonl_path):,} bytes): Complete JSONL document records.",
        f"2. **`rag_chunks.jsonl`** ({os.path.getsize(chunks_jsonl_path):,} bytes): Streaming JSONL chunks.",
        f"3. **`rag_chunks.parquet`** ({os.path.getsize(chunks_parquet_path):,} bytes): Columnar compressed parquet index."
    ])

    with open(rep_dir / "rag_preparation_report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(rep_lines) + "\n")

    logger.info("RAG preparation completed successfully.")
    return summary


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Prepare RAG document and chunk indexes.")
    parser.add_argument("--data-path", default="cleaned/cleaned_patents_consolidated.parquet", help="Cleaned dataset path")
    parser.add_argument("--rag-dir", default="cleaned/rag", help="RAG output folder")
    parser.add_argument("--reports-dir", default="reports", help="Reports folder")
    args = parser.parse_args()

    d_p = args.data_path
    r_g = args.rag_dir
    r_d = args.reports_dir
    if not os.path.exists(d_p) and os.path.exists(os.path.join("miniproject", d_p)):
        d_p = os.path.join("miniproject", d_p)
        r_g = os.path.join("miniproject", r_g)
        r_d = os.path.join("miniproject", r_d)

    summary = build_rag_corpus(
        cleaned_parquet_path=d_p,
        output_rag_dir=r_g,
        reports_dir=r_d
    )
    print("\nRAG preparation completed successfully!")
    print(f"Total Documents: {summary['total_documents']:,} | Total Chunks: {summary['total_chunks']:,}")
