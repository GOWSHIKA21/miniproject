# PatentGraph AI - MongoDB Atlas Migration Report

- **Execution Mode**: `test-batch`
- **Execution Timestamp**: `2026-10-27T05:13:41.155757+00:00` to `2026-10-27T05:13:48.361189+00:00` (7.21s)
- **Target Database**: `patentgraph_db`
- **Target Collection**: `patents`
- **Target Cluster URI**: `mongodb+srv:****@cluster0.s8wie4s.mongodb.net/`

---

## 1. Summary Statistics

| Metric | Value |
| :--- | :--- |
| **Source File** | `cleaned_patents_consolidated.parquet` |
| **Source File SHA-256** | `e79bfdd564c73fecfb84f5f1bf0454e9c390dfd105b9430e69f81ebc9dd27456` |
| **Source Total Records** | 151,438 |
| **Processed Records** | 100 |
| **Newly Upserted Documents** | 100 |
| **Matched / Modified Documents** | 0 |
| **Skipped / Invalid Records** | 0 |
| **Failed Records** | 0 |
| **Initial Target Count** | 0 |
| **Final Target Count** | 100 |

---

## 2. Indexes Verified

- `idx_patent_id_unique`
- `idx_field_of_invention`
- `idx_ipo_location`
- `idx_filing_date`
- `idx_publication_date`
- `idx_application_type`

---

## 3. Quarantined / Skipped Records

No records skipped. All records passed validation.
