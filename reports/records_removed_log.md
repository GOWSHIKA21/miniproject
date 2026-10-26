# PatentGraph AI — Quarantined Records Log

In accordance with autonomous data safety rules, no original source records were deleted.
Instead, corrupted records that lacked mandatory semantic attributes were separated into quarantine for auditing.

**Total Records Quarantined**: `1`  

| Source File | Row Index | Application Number | Publication Number | Raw Title | Quarantine Reason |
| :--- | :---: | :--- | :--- | :--- | :--- |
| `application_details_granted_2021.csv` | 28365 | `3568/MUMNP/2015` | `52/2021` | `nan` | Missing or invalid TITLE_OF_INVENTION (raw: nan) |

### Resolution & Downstream Impact
- This record possesses no invention title in the official InPASS gazette extract.
- Preserving this record in the active semantic index would cause retrieval anomalies and vector indexing failures.
- The record is preserved in `cleaned/quarantined_records.csv` and `cleaned/quarantined_records.json` for full historical auditability.
