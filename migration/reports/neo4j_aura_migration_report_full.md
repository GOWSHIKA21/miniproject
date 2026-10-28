# PatentGraph AI - Neo4j Aura Migration Report

- **Execution Mode**: `full`
- **Cluster URI**: `neo4j+s://f53f0d18.databases.neo4j.io`
- **Database**: `f53f0d18`
- **Username**: `f53f0d18`
- **Transport**: `HTTPS Query API (Port 443)`
- **Duration**: `556.71`s

## Nodes Ingested
- **Field**: 16
- **Location**: 4
- **ApplicationType**: 9
- **Concept**: 8,211
- **Patent**: 151,438

## Relationships Ingested
- **CLASSIFIED_IN**: 151,438
- **FILED_AT**: 151,438
- **TYPE_OF**: 151,438
- **RELATES_TO**: 101,834
- **CO_OCCURS_WITH**: 13,626

## Constraints & Indexes
- `patent_id_unique`
- `field_id_unique`
- `location_id_unique`
- `type_id_unique`
- `concept_id_unique`
- `patent_field_idx`
- `patent_filing_idx`

## Status / Errors
- ✅ Successfully completed without errors.
