# PatentGraph AI - Qdrant Cloud Migration Report

- **Execution Mode**: `test-batch`
- **Target URL**: `https://f926cdb3-3b12-47ea-9d60-e29fb6b159ff.ca-central-1-0.aws.cloud.qdrant.io`
- **Collection**: `patent_embeddings`
- **Vector Dimension**: 384
- **Distance Metric**: `Cosine`
- **Duration**: `0.0`s

## Migration Summary
- **Points Prepared**: 0
- **Points Upserted**: 0
- **Source**: `faiss` (reused precomputed FAISS vectors)
- **ID Strategy**: Deterministic UUIDv5 namespace mapping (100% idempotent)
