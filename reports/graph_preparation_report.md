# PatentGraph AI — Knowledge Graph Preparation Report

**Generated**: `2026-10-26T22:34:46.650917`  
**Graph Storage Directory**: `C:\Users\gowsh\OneDrive\Desktop\RAG\miniproject\cleaned\graph`  
**Total Nodes Prepared**: `159,678`  
**Total Edges Prepared**: `569,774`  
**Referential Integrity Status**: `PASSED (0 dangling edges)`  

---

## 1. Entity Node Classes

| Node Label | Record Count | Primary Identifier | Key Attributes |
| :--- | :---: | :--- | :--- |
| `Patent` | 151,438 | `patent_id` (e.g. `10/DEL/2010`) | `title`, `field_of_invention`, `ipo_location`, `filing_date`, `publication_date`, `pendency_days`, `claims` |
| `Field` | 16 | `field_id` (e.g. `FIELD_CHEMISTRY`) | `field_name`, `patent_count` |
| `Location` | 4 | `location_id` (e.g. `LOC_DELHI`) | `city`, `office_code`, `patent_count` |
| `ApplicationType` | 9 | `type_id` (e.g. `TYPE_PCT_NATIONAL_PHASE`) | `type_name`, `category`, `patent_count` |
| `Concept` | 8,211 | `concept_id` (e.g. `CONCEPT_POWER_FLOW`) | `concept_name`, `patent_count` |

---

## 2. Relationship Edges

| Relationship Type | Source Entity | Target Entity | Edge Count | Semantics |
| :--- | :--- | :--- | :---: | :--- |
| `CLASSIFIED_IN` | `Patent` | `Field` | 151,438 | Categorizes invention into technical discipline |
| `FILED_AT` | `Patent` | `Location` | 151,438 | Identifies jurisdiction branch office |
| `TYPE_OF` | `Patent` | `ApplicationType` | 151,438 | Procedural patent legal filing type |
| `RELATES_TO` | `Patent` | `Concept` | 101,834 | Connects patent to key technical concept bigram |
| `CO_OCCURS_WITH` | `Concept` | `Field` | 13,626 | Concept cross-domain association weight |

---

## 3. Top 20 Most Frequent Technical Concepts in Corpus

| Rank | Technical Concept | Associated Patents |
| :---: | :--- | :---: |
| 1 | `SYSTEMS METHODS` | 841 |
| 2 | `INTERNAL COMBUSTION` | 575 |
| 3 | `STEEL SHEET` | 524 |
| 4 | `WIRELESS COMMUNICATION` | 496 |
| 5 | `WIND TURBINE` | 404 |
| 6 | `COMPOSITIONS METHODS` | 396 |
| 7 | `METHODS SYSTEMS` | 394 |
| 8 | `COMBUSTION ENGINE` | 348 |
| 9 | `EXHAUST GAS` | 346 |
| 10 | `BASE STATION` | 318 |
| 11 | `POWER SUPPLY` | 287 |
| 12 | `HIGH STRENGTH` | 256 |
| 13 | `ORAL CARE` | 247 |
| 14 | `LIGHT EMITTING` | 218 |
| 15 | `HEAT EXCHANGER` | 215 |
| 16 | `CIRCUIT BREAKER` | 205 |
| 17 | `USER EQUIPMENT` | 202 |
| 18 | `DATA TRANSMISSION` | 181 |
| 19 | `MOTOR VEHICLE` | 181 |
| 20 | `TYPE VEHICLE` | 173 |

---

## 4. Neo4j Batch Ingestion Instructions
1. Copy all CSV files from `cleaned/graph/` to your Neo4j `import/` directory.
2. Execute the generated Cypher script located at `cleaned/graph/neo4j_import.cypher` via `cypher-shell` or Neo4j Browser:
```bash
cypher-shell -u neo4j -p <password> -f cleaned/graph/neo4j_import.cypher
```
3. All constraints, transactional batches (5,000 rows/batch), and label mappings are pre-configured.
