# PatentGraph AI - Cloud Migration Toolkit

Complete tooling for migrating **MongoDB Atlas**, **Neo4j Aura**, and **Qdrant Cloud / Vector Search** for the **PatentGraph AI** system.

---

## 1. Cloud Architecture Overview

```
                      +------------------------------------------+
                      |         React Frontend (:5173)           |
                      +--------------------+---------------------+
                                           |
                                           v
                      +--------------------+---------------------+
                      |         FastAPI Backend (:8000)          |
                      +----+---------------+---------------+-----+
                           |               |               |
           +---------------+               |               +---------------+
           v                               v                               v
+--------------------+           +--------------------+           +--------------------+
|   MongoDB Atlas    |           |     Neo4j Aura     |           |    Qdrant Cloud    |
| (Document Metadata)|           |  (Knowledge Graph) |           |  (Vector Database) |
+--------------------+           +--------------------+           +--------------------+
| 151,438 Patents    |           | 159,678 Nodes      |           | 384-dim Embeddings |
| Full 25 Fields     |           | 569,774 Edges      |           | Cosine Similarity  |
| 6 B-Tree Indexes   |           | 5 Uniqueness Rules |           | Payload Filtering  |
+--------------------+           +--------------------+           +--------------------+
```

---

## 2. Environment Configuration

The single source of truth for backend and migration configuration is:
`miniproject/backend/.env`

Sample template (`miniproject/migration/.env.example`):

```dotenv
# ==============================================================================
# 1. MongoDB Atlas Configuration (Authoritative Documents & Metadata - Preserved)
# ==============================================================================
MONGODB_URI="mongodb+srv://<username>:<password>@cluster0.s8wie4s.mongodb.net/?retryWrites=true&w=majority"
MONGODB_DATABASE="patentgraph_db"
MONGODB_COLLECTION="patents"

# ==============================================================================
# 2. Neo4j Aura Configuration (Patent Knowledge Graph)
# ==============================================================================
# Official Aura URI format: neo4j+s://<dbid>.databases.neo4j.io
# NOTE: Ensure instance is Resumed (Active) in https://console.neo4j.io
NEO4J_URI="neo4j+s://f53f0d18.databases.neo4j.io"
NEO4J_USERNAME="neo4j"
NEO4J_USER="neo4j"
NEO4J_PASSWORD="<your-aura-password>"
NEO4J_DATABASE="neo4j"

# ==============================================================================
# 3. Qdrant Cloud Configuration (Patent Embeddings & Vector Search)
# ==============================================================================
# Format: https://<cluster-id>.<region>.aws.cloud.qdrant.io (HTTPS port 443; do NOT add :6333)
QDRANT_URL="https://f926cdb3-3b12-47ea-9d60-e29fb6b159ff.ca-central-1-0.aws.cloud.qdrant.io"
# IMPORTANT: Paste your secret API key token here (NOT the cluster URL!)
QDRANT_API_KEY="<your-secret-qdrant-api-key-token>"
QDRANT_COLLECTION="patent_embeddings"
```

---

## 3. Dedicated Connectivity Diagnostics

Before attempting any migrations, run the standalone diagnostics to isolate and verify each service independently:

### 3.1. Test Neo4j Aura Connectivity
```powershell
python miniproject/migration/test_neo4j_conn.py
```
- Tests TCP reachability on port 7687 and port 443.
- If **port 7687 is refused / closed**: The Aura Free instance is currently **paused**. Log into [https://console.neo4j.io](https://console.neo4j.io), locate instance `f53f0d18`, and click **"Resume"**. Wait ~60 seconds for status to change to **Running**.
- Tests driver authentication and executes `RETURN 1 AS status`.
- If **AuthError**: Check or reset your password in the Aura Console and update `NEO4J_PASSWORD` in `backend/.env`.

### 3.2. Test Qdrant Cloud Connectivity
```powershell
python miniproject/migration/test_qdrant_conn.py
```
- Normalizes endpoint URL (removes `:6333` if accidentally appended).
- Validates that `QDRANT_API_KEY` is a secret token and **not** a URL.
- Pings the cluster via `client.get_collections()` and inspects collection `patent_embeddings`.
- If **HTTP 403 Forbidden**: In the [Qdrant Cloud Console](https://cloud.qdrant.io), select your cluster `f926cdb3`, open the **API Keys** tab, generate or copy your secret API key token, and paste it into line 20 of `miniproject/backend/.env`.

### 3.3. Unified Cloud Verification
```powershell
python miniproject/migration/verify_cloud_services.py
```
Tests MongoDB Atlas, Neo4j Aura, and Qdrant Cloud together and exports a JSON report to `miniproject/migration/reports/cloud_verification_report.json`.

---

## 4. Migration Commands & Execution

### 4.1. Knowledge Graph Migration to Neo4j Aura (`migrate_graph_to_aura.py`)

1. **Pre-flight Dry Run** (Validates 159,678 nodes and 569,774 edges without writing):
   ```powershell
   python miniproject/migration/migrate_graph_to_aura.py --dry-run
   ```

2. **Test Batch** (Upsert 100 sample nodes & relationships):
   ```powershell
   python miniproject/migration/migrate_graph_to_aura.py --test-batch 100
   ```

3. **Full Migration** (Batches of 2,000 using parameterized Cypher `MERGE`):
   ```powershell
   python miniproject/migration/migrate_graph_to_aura.py --full
   ```
   *(Note for Aura Free tier: to stay comfortably within the 200,000 node limit, use `--limit 50000`)*

---

### 4.2. Vector Migration to Qdrant Cloud (`migrate_vectors_to_qdrant.py`)

1. **Pre-flight Dry Run** (Reuses 2,000 precomputed 384-dim vectors from FAISS):
   ```powershell
   python miniproject/migration/migrate_vectors_to_qdrant.py --dry-run
   ```

2. **Test Batch** (Upsert 50 sample vectors with payloads):
   ```powershell
   python miniproject/migration/migrate_vectors_to_qdrant.py --test-batch 50
   ```

3. **Full Migration of Precomputed Vectors**:
   ```powershell
   python miniproject/migration/migrate_vectors_to_qdrant.py --full
   ```

4. **Encode & Ingest Additional Patents** (from parquet using `all-MiniLM-L6-v2`):
   ```powershell
   python miniproject/migration/migrate_vectors_to_qdrant.py --source parquet --limit 15000
   ```

---

## 5. Safety Guarantees & Resilience

- **MongoDB Atlas Preservation**: The existing MongoDB Atlas configuration, collections, schemas, and queries are 100% preserved.
- **Idempotency**: All ingestion scripts use `MERGE` (Cypher), deterministic UUIDv5 point IDs (Qdrant), and `UpdateOne(..., upsert=True)` (MongoDB).
- **Graceful Cloud Fallback**: If either Neo4j Aura or Qdrant Cloud is temporarily unreachable, the backend transparently falls back to local NetworkX (`knowledge_graph.pkl`) and local FAISS (`faiss_index.bin`) without throwing 500 errors.
- **Credential Protection**: Connection URIs, API keys, and passwords are automatically masked in all logs, exceptions, and reports.
