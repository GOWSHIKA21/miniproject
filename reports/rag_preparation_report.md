# PatentGraph AI — RAG Retrieval Corpus Preparation Report

**Generated**: `2026-10-26T22:35:24.256750`  
**RAG Storage Directory**: `C:\Users\gowsh\OneDrive\Desktop\RAG\miniproject\cleaned\rag`  
**Total Patent Documents**: `151,438`  
**Total Semantic Chunks**: `454,314`  
**Unique Chunk Identifiers**: `454,314`  
**Duplicate Chunks**: `0`  
**Empty Chunks**: `0`  

---

## 1. Chunk Length & Word Count Distributions

- **Average Words per Chunk**: `25.09` words  
- **Minimum Words**: `12` words  
- **Maximum Words**: `78` words  

| Semantic Section | Chunk Count | Purpose in Retrieval |
| :--- | :---: | :--- |
| `invention_overview` | 151,438 | Semantic matching on technological claims and invention concepts |
| `procedural_history` | 151,438 | Filtering and QA over IPO office jurisdiction, filing/grant timeline, and legal procedure |
| `scope_and_claims` | 151,438 | Quantitative queries on claims scope, specification length, and IPO gazette verification |

---

## 2. Chunk Identification & Schema
Every chunk follows the canonical schema:
- `chunk_id`: Deterministic composite `{patent_id}#{section_slug}` (e.g. `10/DEL/2010#c_invention`).
- `patent_id`: Foreign key link to canonical patent entity.
- `section`: Segment taxonomy indicator.
- `chunk_text`: Natural language text chunk.
- `char_count` & `word_count`: Exact length metrics.
- `field_of_invention`, `ipo_location`, `filing_date`, `publication_date`: Retained metadata for pre/post-retrieval filtering.
- `source_file` & `source_url`: Full provenance and official IPO gazette ground-truth evidence link.

---

## 3. Storage Formats Prepared
1. **`rag_documents.jsonl`** (172,383,961 bytes): Complete JSONL document records.
2. **`rag_chunks.jsonl`** (273,227,439 bytes): Streaming JSONL chunks.
3. **`rag_chunks.parquet`** (24,384,661 bytes): Columnar compressed parquet index.
