# PatentGraph AI — Consolidated Data Quality & Corpus Summary

## Executive Summary

The PatentGraph AI data cleaning, standardization, and knowledge graph/RAG preparation pipeline was executed autonomously from end to end. The corpus represents the complete Indian Patent Office (InPASS) gazette extracts of granted patents spanning 2016 through 2023.

### Key Metrics at a Glance

| Metric | Raw Ingested | Cleaned & Prepared | Notes |
| :--- | :---: | :---: | :--- |
| **Total Datasets** | 8 CSV files | 8 CSVs + 1 Consolidated Parquet + 1 Consolidated CSV | Raw files 100% preserved |
| **Total Records** | 151,439 | 151,438 valid (1 quarantined) | 1 corrupted record separated to quarantine |
| **Exact Duplicate Rows** | 0 | 0 | Zero duplicate rows in raw corpus |
| **Duplicate Patent IDs** | 0 | 0 | 100% unique primary keys |
| **Knowledge Graph Nodes** | N/A | 159,678 nodes | 5 entity types: Patent, Field, Location, Type, Concept |
| **Knowledge Graph Edges** | N/A | 569,774 edges | 5 relationship types with 0 dangling references |
| **RAG Retrieval Documents**| N/A | 151,438 docs | Full structured evidence representation |
| **RAG Semantic Chunks** | N/A | 454,314 chunks | 3 structured chunks per patent |
| **Unparsable Dates** | 0 | 0 | 100% parsed to ISO 8601 (YYYY-MM-DD) |
| **Negative Pendencies** | 0 | 0 | 100% chronological consistency |

---

## Technology Domain Coverage

| Field of Invention | Valid Records | Percentage | Median Claims | Median Pages |
| :--- | :---: | :---: | :---: | :---: |
| CHEMISTRY | 38,871 | 25.67% | 14 | 29 |
| MECHANICAL | 32,828 | 21.68% | 11 | 24 |
| ELECTRONICS | 14,591 | 9.63% | 18 | 33 |
| ELECTRICAL | 12,199 | 8.06% | 12 | 25 |
| COMMUNICATION | 7,972 | 5.26% | 20 | 36 |
| POLYMER | 7,852 | 5.18% | 15 | 30 |
| COMPUTER | 7,342 | 4.85% | 17 | 32 |
| PHYSICS | 7,308 | 4.83% | 15 | 28 |
| BIOTECHNOLOGY | 6,016 | 3.97% | 19 | 51 |
| BIOMEDICAL | 5,232 | 3.45% | 15 | 30 |
| METALLURGY | 3,313 | 2.19% | 10 | 27 |
| TEXTILE | 2,369 | 1.56% | 14 | 25 |
| BIOCHEMISTRY | 2,055 | 1.36% | 18 | 43 |
| CIVIL | 2,017 | 1.33% | 13 | 24 |
| FOOD | 1,248 | 0.82% | 14 | 25 |
| UNCATEGORIZED | 225 | 0.15% | 14 | 29 |

---

## IPO Branch Office Distribution

| IPO Branch Office | Branch Code | Total Granted Patents | Percentage |
| :--- | :---: | :---: | :---: |
| IPO Delhi | `DEL` | 57,345 | 37.87% |
| IPO Chennai | `CHE` | 48,987 | 32.35% |
| IPO Kolkata | `KOL` | 23,368 | 15.43% |
| IPO Mumbai | `MUM` | 21,738 | 14.35% |

---

## Application Procedure Classification

| Application Category | Total Patents | Percentage | Primary Route |
| :--- | :---: | :---: | :--- |
| PCT National Phase | 102,586 | 67.74% | International Patent Cooperation Treaty (PCT) route into India |
| Ordinary | 30,848 | 20.37% | Direct national filing at Indian Patent Office |
| Convention | 15,493 | 10.23% | Paris Convention priority route from foreign member country |
| Divisional | 2,310 | 1.53% | Divided out of parent patent application |
| Patent of Addition | 201 | 0.13% | Improvement or modification of already-filed parent patent |

---

## Verification and Preservation Statement
1. **Safety Guarantee**: Original raw CSV datasets (`dataset/application_details_granted_2016.csv` through `2023.csv`) were never modified, moved, or deleted. All SHA-256 checksums match pre-audit values.
2. **Idempotence Guarantee**: Rerunning the cleaning scripts produces identical, deterministic output files without accumulating duplicate records.
3. **Downstream Ready**: The generated Parquet datasets, Neo4j graph files, and RAG retrieval chunks are immediately usable by FastAPI backend, FAISS vector indexer, BM25 retriever, and ML classification pipelines.
