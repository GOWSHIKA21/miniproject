// PatentGraph AI - Neo4j Data Ingestion Cypher Script
// Generated: 2026-10-26T22:34:46.642459
// Assumes CSV files are in the Neo4j import/ directory or file URL

// Step 1: Create Constraints and Indexes
CREATE CONSTRAINT patent_id_unique IF NOT EXISTS FOR (p:Patent) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT field_id_unique IF NOT EXISTS FOR (f:Field) REQUIRE f.id IS UNIQUE;
CREATE CONSTRAINT location_id_unique IF NOT EXISTS FOR (l:Location) REQUIRE l.id IS UNIQUE;
CREATE CONSTRAINT type_id_unique IF NOT EXISTS FOR (t:ApplicationType) REQUIRE t.id IS UNIQUE;
CREATE CONSTRAINT concept_id_unique IF NOT EXISTS FOR (c:Concept) REQUIRE c.id IS UNIQUE;

CREATE INDEX patent_field_idx IF NOT EXISTS FOR (p:Patent) ON (p.field);
CREATE INDEX patent_filing_idx IF NOT EXISTS FOR (p:Patent) ON (p.filing_date);

// Step 2: Load Nodes
LOAD CSV WITH HEADERS FROM 'file:///nodes_fields.csv' AS row
MERGE (f:Field {id: row['id:ID(Field-ID)']})
SET f.name = row.field_name, f.patent_count = toInteger(row.patent_count);

LOAD CSV WITH HEADERS FROM 'file:///nodes_locations.csv' AS row
MERGE (l:Location {id: row['id:ID(Location-ID)']})
SET l.city = row.city, l.office_code = row.office_code, l.patent_count = toInteger(row.patent_count);

LOAD CSV WITH HEADERS FROM 'file:///nodes_application_types.csv' AS row
MERGE (t:ApplicationType {id: row['id:ID(Type-ID)']})
SET t.name = row.type_name, t.category = row.category, t.patent_count = toInteger(row.patent_count);

LOAD CSV WITH HEADERS FROM 'file:///nodes_concepts.csv' AS row
MERGE (c:Concept {id: row['id:ID(Concept-ID)']})
SET c.name = row.concept_name, c.patent_count = toInteger(row.patent_count);

:auto
LOAD CSV WITH HEADERS FROM 'file:///nodes_patents.csv' AS row
CALL {
  WITH row
  MERGE (p:Patent {id: row['id:ID(Patent-ID)']})
  SET p.title = row.title,
      p.field = row.field_of_invention,
      p.location = row.ipo_location,
      p.application_type = row.application_type,
      p.filing_date = row.filing_date,
      p.publication_date = row.publication_date,
      p.pendency_days = toInteger(row.pendency_days),
      p.no_of_claims = toInteger(row.no_of_claims),
      p.no_of_pages = toInteger(row.no_of_pages),
      p.source_url = row.source_url
} IN TRANSACTIONS OF 5000 ROWS;

// Step 3: Load Relationships
:auto
LOAD CSV WITH HEADERS FROM 'file:///edges_classified_in.csv' AS row
CALL {
  WITH row
  MATCH (p:Patent {id: row[':START_ID(Patent-ID)']})
  MATCH (f:Field {id: row[':END_ID(Field-ID)']})
  MERGE (p)-[:CLASSIFIED_IN]->(f)
} IN TRANSACTIONS OF 5000 ROWS;

:auto
LOAD CSV WITH HEADERS FROM 'file:///edges_filed_at.csv' AS row
CALL {
  WITH row
  MATCH (p:Patent {id: row[':START_ID(Patent-ID)']})
  MATCH (l:Location {id: row[':END_ID(Location-ID)']})
  MERGE (p)-[:FILED_AT]->(l)
} IN TRANSACTIONS OF 5000 ROWS;

:auto
LOAD CSV WITH HEADERS FROM 'file:///edges_type_of.csv' AS row
CALL {
  WITH row
  MATCH (p:Patent {id: row[':START_ID(Patent-ID)']})
  MATCH (t:ApplicationType {id: row[':END_ID(Type-ID)']})
  MERGE (p)-[:TYPE_OF]->(t)
} IN TRANSACTIONS OF 5000 ROWS;

:auto
LOAD CSV WITH HEADERS FROM 'file:///edges_relates_to.csv' AS row
CALL {
  WITH row
  MATCH (p:Patent {id: row[':START_ID(Patent-ID)']})
  MATCH (c:Concept {id: row[':END_ID(Concept-ID)']})
  MERGE (p)-[:RELATES_TO]->(c)
} IN TRANSACTIONS OF 5000 ROWS;

:auto
LOAD CSV WITH HEADERS FROM 'file:///edges_co_occurs_with.csv' AS row
CALL {
  WITH row
  MATCH (c:Concept {id: row[':START_ID(Concept-ID)']})
  MATCH (f:Field {id: row[':END_ID(Field-ID)']})
  MERGE (c)-[r:CO_OCCURS_WITH]->(f)
  SET r.weight = toInteger(row.weight)
} IN TRANSACTIONS OF 5000 ROWS;
