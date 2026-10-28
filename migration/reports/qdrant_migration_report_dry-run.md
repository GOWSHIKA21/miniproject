# PatentGraph AI - Qdrant Cloud Migration Report

- **Execution Mode**: `dry-run`
- **Target URL**: `https://f926cdb3-3b12-47ea-9d60-e29fb6b159ff.ca-central-1-0.aws.cloud.qdrant.io`
- **Collection**: `patent_embeddings`
- **Vector Dimension**: 384
- **Distance Metric**: `Cosine`
- **Duration**: `3.31`s

## Migration Summary
- **Points Prepared**: 2,000
- **Points Upserted**: 0
- **Source**: `faiss` (reused precomputed FAISS vectors)
- **ID Strategy**: Deterministic UUIDv5 namespace mapping (100% idempotent)
