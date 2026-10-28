# PatentGraph AI - MongoDB Atlas Backend Integration Plan

This document outlines the step-by-step strategy for transitioning the **PatentGraph AI** FastAPI backend from local Parquet fallback mode to **MongoDB Atlas**.

---

## 1. Architectural Overview

```mermaid
flowchart TD
    User([React Frontend :5173]) -->|Search / Ask / Browse| API[FastAPI Backend :8000]

    subgraph Retrieval Pipeline
        API -->|Vector Similarity| FAISS[FAISS FlatIP Index (Local)]
        API -->|Keyword BM25| BM25[Rank-BM25 Index (Local)]
        API -->|Graph Expansion| KG[Knowledge Graph NetworkX / Neo4j]
        FAISS & BM25 & KG -->|RRF Merged Patent IDs| MergedIDs[Top Candidate IDs]
    end

    subgraph Metadata & Grounding Layer
        MergedIDs --> MongoDecision{MongoDB Atlas Connected?}
        MongoDecision -->|Yes| Atlas[(MongoDB Atlas Cluster: 'patents')]
        MongoDecision -->|No / Offline| ParquetFallback[Local Parquet Storage (Fallback)]
    end

    subgraph Synthesis Layer
        Atlas & ParquetFallback --> Assembler[Evidence Assembler]
        Assembler --> LLM[Groq Llama-3.3 / Fallback Synthesizer]
        LLM --> FrontendResponse[Verified Answer with Citations]
    end
```

---

## 2. Environment Configuration

The backend natively supports MongoDB Atlas via environment variables loaded through `python-dotenv` and Pydantic Settings (`backend.app.core.config.Settings`):

```dotenv
# MongoDB Atlas Connection
MONGODB_URI="mongodb+srv://<username>:<password>@<cluster-url>/?retryWrites=true&w=majority&appName=PatentGraphAI"
MONGODB_DATABASE="patentgraph_db"
MONGODB_COLLECTION="patents"
```

### Connection String Security
- Credentials are automatically masked in all log outputs (`mongodb+srv://<user>:****@<cluster>`).
- `.env` is strictly excluded from Git tracking via `.gitignore`.
- Placeholders are documented in `.env.example`.

---

## 3. Database Connection & Connection Pooling

In `backend/app/database/mongodb.py`, `MongoDBClient` manages the PyMongo client with recommended Atlas connection pooling parameters:

```python
MongoClient(
    self.uri,
    maxPoolSize=50,
    minPoolSize=5,
    serverSelectionTimeoutMS=3000,
    connectTimeoutMS=3000,
    socketTimeoutMS=20000,
    retryWrites=True,
    w="majority"
)
```

### Health & Lifespan Hooks
On FastAPI startup (`backend/app/main.py`), the backend automatically checks Atlas connectivity during the lifespan event:
- If connected: Logs `MongoDB Status: Connected`, verifies indexes, and routes all metadata requests to Atlas.
- If offline/unreachable: Logs `MongoDB Status: Offline (Parquet fallback active)` and seamlessly falls back to `backend/app/data/cleaned_patents.parquet` without crashing the application.

---

## 4. Query Routing & Optimization

### 4.1. Fast Batch Retrieval for Hybrid RAG (`patent_service.get_patents_batch`)
When FAISS and BM25 identify the top candidate patent IDs (e.g. 5 to 50 IDs), the backend retrieves the full patent metadata using an indexed batch query:
```python
coll = self.db[self.collection_name]
cursor = coll.find(
    {"patent_id": {"$in": candidate_ids}},
    {"_id": 0}  # Exclude internal _id for network bandwidth optimization
)
```
- **Index Utilized**: `idx_patent_id_unique` (O(1) B-tree lookup per ID).
- **Latency**: Under 15-25 ms round-trip to Atlas.

### 4.2. Exact Single Patent Details (`/api/patents/{id}`)
```python
doc = self.db[self.collection_name].find_one({"patent_id": patent_id}, {"_id": 0})
```
- Returns the complete 25-field document, formatted into `PatentFrontendFormat` for React cards and details modals.

### 4.3. Structured Browsing & Faceted Search (`mongo_client.search_patents`)
When users filter patents by domain, IPO location, application type, or filing date range without full-text queries:
```python
coll.find(mongo_query, {"_id": 0}).sort(sort_order).skip(skip_n).limit(page_size)
```
- Uses compound-compatible single indexes on `field_of_invention`, `ipo_location`, `filing_date`, and `publication_date`.
- Performs exact server-side counting with `count_documents(mongo_query)`.

---

## 5. Rollout & Cutover Procedure

1. **Step 1 - Create Atlas Cluster**:
   - Provision an M0 Free Tier cluster in the closest AWS/GCP region (e.g., `ap-south-1` Mumbai).
   - Create a database user with `readWrite` access to `patentgraph_db`.
   - Whitelist the backend host IP (or `0.0.0.0/0` with secure password for development).

2. **Step 2 - Run Migration**:
   - Execute dry-run: `python miniproject/migration/migrate_to_atlas.py --dry-run`
   - Execute test batch: `python miniproject/migration/migrate_to_atlas.py --test-batch 100`
   - Verify test batch: `python miniproject/migration/verify_atlas.py`
   - Complete full upload: `python miniproject/migration/migrate_to_atlas.py --full`

3. **Step 3 - Switch Backend to Atlas**:
   - Update `miniproject/backend/.env` with the Atlas `MONGODB_URI`.
   - Start the FastAPI backend:
     ```powershell
     python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
     ```
   - Verify via `/api/health`: Ensure `mongodb.connected == true` and `total_documents == 151438`.

4. **Step 4 - Verify End-to-End Pipeline**:
   - Run automated test suite: `python -m pytest backend/tests/test_api.py -v`.
   - Test UI search, React Flow graph explorer, and RAG chat in browser (`http://localhost:5173`).
