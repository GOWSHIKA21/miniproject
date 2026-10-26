# PatentGraph AI — Automated Validation Suite Report

**Validation Timestamp**: `2026-10-26T22:35:32.642049`  
**Overall Status**: `PASSED (All 8 Test Suites Succeeded)`  

---

## Validation Checklist Results

| Test Suite | Status | Validation Result & Metrics |
| :--- | :---: | :--- |
| **Original Source Files Preservation** | `PASSED` | All 8 original CSV files matched pre-audit SHA-256 hashes with 100% byte fidelity. |
| **Record Counts & Reconciliation** | `PASSED` | Raw (151,439) = Cleaned Parquet (151,438) + Cleaned CSV (151,438) + Quarantined (1). Exact match. |
| **Primary Key Integrity & Identifier Formatting** | `PASSED` | 151,438 unique primary keys. 0 nulls, 0 duplicates. 100% conform to official Indian Patent numbering (110,158 standard slash, 41,274 12-digit CBR, 6 early PCT; e.g. 201847018175). |
| **Date Standardization & Chronological Order** | `PASSED` | 100% of dates conform to ISO 8601 (YYYY-MM-DD). 0 chronological violations (pub_date >= filing_date). 0 negative pendencies. |
| **Text Normalization & Symbol Preservation** | `PASSED` | 0 null/empty titles, 0 corrupt characters, 0 unstripped outer quotes. Scientific symbols preserved (10 degree signs, 6 plus-minus signs, 0 micro signs). |
| **Knowledge Graph Referential Integrity** | `PASSED` | 159,678 nodes across 5 entity types. 569,774 edges across 5 relationship types. Exactly 0 dangling or orphaned endpoints. |
| **RAG Documents & Chunk Retrieval Index** | `PASSED` | 151,438 documents and 454,314 chunks. 100% unique chunk IDs. 0 empty chunks. 100% link to valid patent IDs. |
| **Source Provenance & Data Lineage** | `PASSED` | 100% of records retain source_file provenance across all 8 annual CSV sources and official IPO verification URLs. |

---

## Detailed Verification Metrics

- **Raw Input Records Audited**: 151,439 records across 8 CSV files (2016–2023).
- **Cleaned Valid Records Persisted**: 151,438 records.
- **Quarantined Records**: 1 record (`3568/MUMNP/2015` with NaN title).
- **Dangling Graph References**: 0 orphaned endpoints.
- **RAG Semantic Chunks**: 454,314 unique chunks with 0 duplicates.
- **Original Datasets Immutability**: 100% byte-for-byte identical (SHA-256 verified).

### Failures / Blocking Issues
None detected. All automated tests executed and verified successfully.
