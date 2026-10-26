#!/usr/bin/env python3
"""
PatentGraph AI - Knowledge Graph Preparation Script
Constructs graph-ready entities and relationships from cleaned Indian Patent data.
Generates:
  - cleaned/graph/nodes_patents.csv
  - cleaned/graph/nodes_fields.csv
  - cleaned/graph/nodes_locations.csv
  - cleaned/graph/nodes_application_types.csv
  - cleaned/graph/nodes_concepts.csv
  - cleaned/graph/edges_classified_in.csv
  - cleaned/graph/edges_filed_at.csv
  - cleaned/graph/edges_type_of.csv
  - cleaned/graph/edges_relates_to.csv
  - cleaned/graph/edges_co_occurs_with.csv
  - cleaned/graph/neo4j_import.cypher
  - cleaned/graph/graph_summary.json
  - reports/graph_preparation_report.md
"""

import os
import sys
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, Any, List, Set, Tuple
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("GraphPreparer")

STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "in", "for", "with", "by", "on", "to", "from",
    "method", "apparatus", "system", "device", "process", "composition", "assembly",
    "thereof", "using", "use", "comprising", "production", "manufacturing", "preparation",
    "improved", "novel", "new", "based", "structure", "mechanism", "providing", "having",
    "material", "materials", "unit", "arrangement", "formed", "wherein", "same", "one"
}


def slugify(text: str) -> str:
    """Create URL/ID-safe slug for entity identifiers."""
    cleaned = re.sub(r'[^a-zA-Z0-9]+', '_', text.strip()).strip('_')
    return cleaned.upper() if cleaned else "UNKNOWN"


def extract_technical_phrases(title: str, max_phrases: int = 3) -> List[str]:
    """Extract 2-word technical bigrams or salient single keywords from title."""
    clean = re.sub(r'[^a-zA-Z0-9\s\-]', ' ', str(title)).lower()
    tokens = [t.strip('-') for t in clean.split() if len(t) > 2 and t not in STOPWORDS]
    
    phrases = []
    # Bigrams
    for i in range(len(tokens) - 1):
        bigram = f"{tokens[i]} {tokens[i+1]}".upper()
        phrases.append(bigram)

    if not phrases and tokens:
        phrases = [t.upper() for t in tokens[:max_phrases]]

    return phrases[:max_phrases]


def prepare_knowledge_graph(
    cleaned_data_path: str = "cleaned/cleaned_patents_consolidated.parquet",
    graph_output_dir: str = "cleaned/graph",
    reports_dir: str = "reports",
    min_concept_frequency: int = 5
) -> Dict[str, Any]:
    """Process cleaned patents and generate Neo4j-ready nodes and edges."""
    data_file = Path(cleaned_data_path).resolve()
    out_dir = Path(graph_output_dir).resolve()
    rep_dir = Path(reports_dir).resolve()

    out_dir.mkdir(parents=True, exist_ok=True)
    rep_dir.mkdir(parents=True, exist_ok=True)

    if not data_file.exists():
        raise FileNotFoundError(f"Cleaned dataset not found at {data_file}")

    logger.info(f"Loading cleaned dataset from {data_file}...")
    df = pd.read_parquet(data_file)
    total_patents = len(df)
    logger.info(f"Loaded {total_patents:,} patent records.")

    # 1. First pass: extract and count concepts to filter noise
    logger.info("Extracting candidate technical concepts across patent titles...")
    concept_patents = defaultdict(set)
    concept_fields = defaultdict(Counter)

    for idx, row in df.iterrows():
        p_id = row["patent_id"]
        field = row["field_of_invention"]
        phrases = extract_technical_phrases(row["title"])
        for phrase in phrases:
            concept_patents[phrase].add(p_id)
            concept_fields[phrase][field] += 1

    # Retain concepts that appear in at least `min_concept_frequency` patents
    frequent_concepts = {
        phrase: p_set for phrase, p_set in concept_patents.items()
        if len(p_set) >= min_concept_frequency
    }
    logger.info(
        f"Filtered concepts: {len(frequent_concepts):,} frequent concepts "
        f"(appearing in >= {min_concept_frequency} patents) retained out of {len(concept_patents):,} raw phrases."
    )

    # 2. Build Nodes DataFrames
    logger.info("Generating entity nodes...")

    # Patent Nodes
    patent_nodes = df[[
        "patent_id", "title", "field_of_invention", "ipo_location", "ipo_code",
        "application_type", "application_category", "filing_date", "publication_date",
        "pendency_days", "no_of_claims", "no_of_pages", "source_url"
    ]].copy()
    patent_nodes.rename(columns={"patent_id": "id:ID(Patent-ID)"}, inplace=True)
    patent_nodes[":LABEL"] = "Patent"

    # Field Nodes
    field_counts = df["field_of_invention"].value_counts().to_dict()
    field_nodes_data = []
    for f_name, count in field_counts.items():
        f_id = f"FIELD_{slugify(f_name)}"
        field_nodes_data.append({
            "id:ID(Field-ID)": f_id,
            "field_name": f_name,
            "patent_count": count,
            ":LABEL": "Field"
        })
    df_field_nodes = pd.DataFrame(field_nodes_data)

    # Location Nodes
    loc_counts = df["ipo_location"].value_counts().to_dict()
    loc_nodes_data = []
    for loc_name, count in loc_counts.items():
        loc_id = f"LOC_{slugify(loc_name)}"
        office_code = df[df["ipo_location"] == loc_name]["ipo_code"].iloc[0] if not df[df["ipo_location"] == loc_name].empty else "OTH"
        loc_nodes_data.append({
            "id:ID(Location-ID)": loc_id,
            "city": loc_name,
            "office_code": office_code,
            "patent_count": count,
            ":LABEL": "Location"
        })
    df_loc_nodes = pd.DataFrame(loc_nodes_data)

    # Application Type Nodes
    type_counts = df["application_type"].value_counts().to_dict()
    type_nodes_data = []
    for t_name, count in type_counts.items():
        t_id = f"TYPE_{slugify(t_name)}"
        cat = df[df["application_type"] == t_name]["application_category"].iloc[0] if not df[df["application_type"] == t_name].empty else "Other"
        type_nodes_data.append({
            "id:ID(Type-ID)": t_id,
            "type_name": t_name,
            "category": cat,
            "patent_count": count,
            ":LABEL": "ApplicationType"
        })
    df_type_nodes = pd.DataFrame(type_nodes_data)

    # Concept Nodes
    concept_nodes_data = []
    for phrase, p_set in frequent_concepts.items():
        c_id = f"CONCEPT_{slugify(phrase)}"
        concept_nodes_data.append({
            "id:ID(Concept-ID)": c_id,
            "concept_name": phrase,
            "patent_count": len(p_set),
            ":LABEL": "Concept"
        })
    df_concept_nodes = pd.DataFrame(concept_nodes_data)

    # 3. Build Edges DataFrames
    logger.info("Generating relationship edges...")

    # Edge: CLASSIFIED_IN (Patent -> Field)
    edges_classified_in = []
    # Edge: FILED_AT (Patent -> Location)
    edges_filed_at = []
    # Edge: TYPE_OF (Patent -> ApplicationType)
    edges_type_of = []
    # Edge: RELATES_TO (Patent -> Concept)
    edges_relates_to = []

    for idx, row in df.iterrows():
        p_id = row["patent_id"]
        f_id = f"FIELD_{slugify(row['field_of_invention'])}"
        loc_id = f"LOC_{slugify(row['ipo_location'])}"
        type_id = f"TYPE_{slugify(row['application_type'])}"

        edges_classified_in.append({
            ":START_ID(Patent-ID)": p_id,
            ":END_ID(Field-ID)": f_id,
            ":TYPE": "CLASSIFIED_IN"
        })
        edges_filed_at.append({
            ":START_ID(Patent-ID)": p_id,
            ":END_ID(Location-ID)": loc_id,
            ":TYPE": "FILED_AT"
        })
        edges_type_of.append({
            ":START_ID(Patent-ID)": p_id,
            ":END_ID(Type-ID)": type_id,
            ":TYPE": "TYPE_OF"
        })

        phrases = extract_technical_phrases(row["title"])
        for phrase in phrases:
            if phrase in frequent_concepts:
                c_id = f"CONCEPT_{slugify(phrase)}"
                edges_relates_to.append({
                    ":START_ID(Patent-ID)": p_id,
                    ":END_ID(Concept-ID)": c_id,
                    ":TYPE": "RELATES_TO"
                })

    df_edges_classified = pd.DataFrame(edges_classified_in)
    df_edges_filed = pd.DataFrame(edges_filed_at)
    df_edges_type = pd.DataFrame(edges_type_of)
    df_edges_relates = pd.DataFrame(edges_relates_to).drop_duplicates()

    # Edge: CO_OCCURS_WITH (Concept -> Field)
    edges_co_occurs = []
    for phrase, f_counter in concept_fields.items():
        if phrase in frequent_concepts:
            c_id = f"CONCEPT_{slugify(phrase)}"
            for field_name, co_count in f_counter.items():
                if co_count >= 2:  # at least 2 co-occurrences
                    f_id = f"FIELD_{slugify(field_name)}"
                    edges_co_occurs.append({
                        ":START_ID(Concept-ID)": c_id,
                        ":END_ID(Field-ID)": f_id,
                        "weight": co_count,
                        ":TYPE": "CO_OCCURS_WITH"
                    })
    df_edges_co_occurs = pd.DataFrame(edges_co_occurs)

    # 4. Save Node CSVs
    logger.info("Persisting node and edge CSV files...")
    patent_nodes.to_csv(out_dir / "nodes_patents.csv", index=False, encoding="utf-8")
    df_field_nodes.to_csv(out_dir / "nodes_fields.csv", index=False, encoding="utf-8")
    df_loc_nodes.to_csv(out_dir / "nodes_locations.csv", index=False, encoding="utf-8")
    df_type_nodes.to_csv(out_dir / "nodes_application_types.csv", index=False, encoding="utf-8")
    df_concept_nodes.to_csv(out_dir / "nodes_concepts.csv", index=False, encoding="utf-8")

    # 5. Save Edge CSVs
    df_edges_classified.to_csv(out_dir / "edges_classified_in.csv", index=False, encoding="utf-8")
    df_edges_filed.to_csv(out_dir / "edges_filed_at.csv", index=False, encoding="utf-8")
    df_edges_type.to_csv(out_dir / "edges_type_of.csv", index=False, encoding="utf-8")
    df_edges_relates.to_csv(out_dir / "edges_relates_to.csv", index=False, encoding="utf-8")
    df_edges_co_occurs.to_csv(out_dir / "edges_co_occurs_with.csv", index=False, encoding="utf-8")

    # 6. Validate Endpoint Integrity (ensure 0 dangling references)
    patent_ids = set(patent_nodes["id:ID(Patent-ID)"])
    field_ids = set(df_field_nodes["id:ID(Field-ID)"])
    loc_ids = set(df_loc_nodes["id:ID(Location-ID)"])
    type_ids = set(df_type_nodes["id:ID(Type-ID)"])
    concept_ids = set(df_concept_nodes["id:ID(Concept-ID)"])

    classified_orphans = (~df_edges_classified[":START_ID(Patent-ID)"].isin(patent_ids)).sum() + (~df_edges_classified[":END_ID(Field-ID)"].isin(field_ids)).sum()
    filed_orphans = (~df_edges_filed[":START_ID(Patent-ID)"].isin(patent_ids)).sum() + (~df_edges_filed[":END_ID(Location-ID)"].isin(loc_ids)).sum()
    type_orphans = (~df_edges_type[":START_ID(Patent-ID)"].isin(patent_ids)).sum() + (~df_edges_type[":END_ID(Type-ID)"].isin(type_ids)).sum()
    relates_orphans = (~df_edges_relates[":START_ID(Patent-ID)"].isin(patent_ids)).sum() + (~df_edges_relates[":END_ID(Concept-ID)"].isin(concept_ids)).sum()
    co_occurs_orphans = (~df_edges_co_occurs[":START_ID(Concept-ID)"].isin(concept_ids)).sum() + (~df_edges_co_occurs[":END_ID(Field-ID)"].isin(field_ids)).sum()

    total_orphans = int(classified_orphans + filed_orphans + type_orphans + relates_orphans + co_occurs_orphans)
    logger.info(f"Integrity check: total orphaned / dangling references = {total_orphans}")

    # 7. Generate Cypher Import Script
    cypher_script = f"""// PatentGraph AI - Neo4j Data Ingestion Cypher Script
// Generated: {datetime.now().isoformat()}
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
MERGE (f:Field {{id: row['id:ID(Field-ID)']}})
SET f.name = row.field_name, f.patent_count = toInteger(row.patent_count);

LOAD CSV WITH HEADERS FROM 'file:///nodes_locations.csv' AS row
MERGE (l:Location {{id: row['id:ID(Location-ID)']}})
SET l.city = row.city, l.office_code = row.office_code, l.patent_count = toInteger(row.patent_count);

LOAD CSV WITH HEADERS FROM 'file:///nodes_application_types.csv' AS row
MERGE (t:ApplicationType {{id: row['id:ID(Type-ID)']}})
SET t.name = row.type_name, t.category = row.category, t.patent_count = toInteger(row.patent_count);

LOAD CSV WITH HEADERS FROM 'file:///nodes_concepts.csv' AS row
MERGE (c:Concept {{id: row['id:ID(Concept-ID)']}})
SET c.name = row.concept_name, c.patent_count = toInteger(row.patent_count);

:auto
LOAD CSV WITH HEADERS FROM 'file:///nodes_patents.csv' AS row
CALL {{
  WITH row
  MERGE (p:Patent {{id: row['id:ID(Patent-ID)']}})
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
}} IN TRANSACTIONS OF 5000 ROWS;

// Step 3: Load Relationships
:auto
LOAD CSV WITH HEADERS FROM 'file:///edges_classified_in.csv' AS row
CALL {{
  WITH row
  MATCH (p:Patent {{id: row[':START_ID(Patent-ID)']}})
  MATCH (f:Field {{id: row[':END_ID(Field-ID)']}})
  MERGE (p)-[:CLASSIFIED_IN]->(f)
}} IN TRANSACTIONS OF 5000 ROWS;

:auto
LOAD CSV WITH HEADERS FROM 'file:///edges_filed_at.csv' AS row
CALL {{
  WITH row
  MATCH (p:Patent {{id: row[':START_ID(Patent-ID)']}})
  MATCH (l:Location {{id: row[':END_ID(Location-ID)']}})
  MERGE (p)-[:FILED_AT]->(l)
}} IN TRANSACTIONS OF 5000 ROWS;

:auto
LOAD CSV WITH HEADERS FROM 'file:///edges_type_of.csv' AS row
CALL {{
  WITH row
  MATCH (p:Patent {{id: row[':START_ID(Patent-ID)']}})
  MATCH (t:ApplicationType {{id: row[':END_ID(Type-ID)']}})
  MERGE (p)-[:TYPE_OF]->(t)
}} IN TRANSACTIONS OF 5000 ROWS;

:auto
LOAD CSV WITH HEADERS FROM 'file:///edges_relates_to.csv' AS row
CALL {{
  WITH row
  MATCH (p:Patent {{id: row[':START_ID(Patent-ID)']}})
  MATCH (c:Concept {{id: row[':END_ID(Concept-ID)']}})
  MERGE (p)-[:RELATES_TO]->(c)
}} IN TRANSACTIONS OF 5000 ROWS;

:auto
LOAD CSV WITH HEADERS FROM 'file:///edges_co_occurs_with.csv' AS row
CALL {{
  WITH row
  MATCH (c:Concept {{id: row[':START_ID(Concept-ID)']}})
  MATCH (f:Field {{id: row[':END_ID(Field-ID)']}})
  MERGE (c)-[r:CO_OCCURS_WITH]->(f)
  SET r.weight = toInteger(row.weight)
}} IN TRANSACTIONS OF 5000 ROWS;
"""
    with open(out_dir / "neo4j_import.cypher", "w", encoding="utf-8") as f:
        f.write(cypher_script)

    # 8. Graph Summary Statistics
    total_nodes = len(patent_nodes) + len(df_field_nodes) + len(df_loc_nodes) + len(df_type_nodes) + len(df_concept_nodes)
    total_edges = len(df_edges_classified) + len(df_edges_filed) + len(df_edges_type) + len(df_edges_relates) + len(df_edges_co_occurs)

    top_concepts = df_concept_nodes.sort_values(by="patent_count", ascending=False).head(20)[["concept_name", "patent_count"]].to_dict(orient="records")

    summary = {
        "generated_timestamp": datetime.now().isoformat(),
        "total_nodes": total_nodes,
        "node_breakdown": {
            "Patent": len(patent_nodes),
            "Field": len(df_field_nodes),
            "Location": len(df_loc_nodes),
            "ApplicationType": len(df_type_nodes),
            "Concept": len(df_concept_nodes)
        },
        "total_edges": total_edges,
        "edge_breakdown": {
            "CLASSIFIED_IN": len(df_edges_classified),
            "FILED_AT": len(df_edges_filed),
            "TYPE_OF": len(df_edges_type),
            "RELATES_TO": len(df_edges_relates),
            "CO_OCCURS_WITH": len(df_edges_co_occurs)
        },
        "integrity_validation": {
            "dangling_or_orphaned_edges": total_orphans,
            "status": "PASSED" if total_orphans == 0 else "FAILED"
        },
        "top_connected_concepts": top_concepts
    }

    with open(out_dir / "graph_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # 9. Markdown Report
    rep_lines = [
        "# PatentGraph AI — Knowledge Graph Preparation Report",
        "",
        f"**Generated**: `{summary['generated_timestamp']}`  ",
        f"**Graph Storage Directory**: `{out_dir}`  ",
        f"**Total Nodes Prepared**: `{total_nodes:,}`  ",
        f"**Total Edges Prepared**: `{total_edges:,}`  ",
        f"**Referential Integrity Status**: `{'PASSED (0 dangling edges)' if total_orphans == 0 else f'FAILED ({total_orphans} orphaned edges)'}`  ",
        "",
        "---",
        "",
        "## 1. Entity Node Classes",
        "",
        "| Node Label | Record Count | Primary Identifier | Key Attributes |",
        "| :--- | :---: | :--- | :--- |",
        f"| `Patent` | {len(patent_nodes):,} | `patent_id` (e.g. `10/DEL/2010`) | `title`, `field_of_invention`, `ipo_location`, `filing_date`, `publication_date`, `pendency_days`, `claims` |",
        f"| `Field` | {len(df_field_nodes):,} | `field_id` (e.g. `FIELD_CHEMISTRY`) | `field_name`, `patent_count` |",
        f"| `Location` | {len(df_loc_nodes):,} | `location_id` (e.g. `LOC_DELHI`) | `city`, `office_code`, `patent_count` |",
        f"| `ApplicationType` | {len(df_type_nodes):,} | `type_id` (e.g. `TYPE_PCT_NATIONAL_PHASE`) | `type_name`, `category`, `patent_count` |",
        f"| `Concept` | {len(df_concept_nodes):,} | `concept_id` (e.g. `CONCEPT_POWER_FLOW`) | `concept_name`, `patent_count` |",
        "",
        "---",
        "",
        "## 2. Relationship Edges",
        "",
        "| Relationship Type | Source Entity | Target Entity | Edge Count | Semantics |",
        "| :--- | :--- | :--- | :---: | :--- |",
        f"| `CLASSIFIED_IN` | `Patent` | `Field` | {len(df_edges_classified):,} | Categorizes invention into technical discipline |",
        f"| `FILED_AT` | `Patent` | `Location` | {len(df_edges_filed):,} | Identifies jurisdiction branch office |",
        f"| `TYPE_OF` | `Patent` | `ApplicationType` | {len(df_edges_type):,} | Procedural patent legal filing type |",
        f"| `RELATES_TO` | `Patent` | `Concept` | {len(df_edges_relates):,} | Connects patent to key technical concept bigram |",
        f"| `CO_OCCURS_WITH` | `Concept` | `Field` | {len(df_edges_co_occurs):,} | Concept cross-domain association weight |",
        "",
        "---",
        "",
        "## 3. Top 20 Most Frequent Technical Concepts in Corpus",
        "",
        "| Rank | Technical Concept | Associated Patents |",
        "| :---: | :--- | :---: |"
    ]
    for idx, c in enumerate(top_concepts, 1):
        rep_lines.append(f"| {idx} | `{c['concept_name']}` | {c['patent_count']:,} |")

    rep_lines.extend([
        "",
        "---",
        "",
        "## 4. Neo4j Batch Ingestion Instructions",
        "1. Copy all CSV files from `cleaned/graph/` to your Neo4j `import/` directory.",
        "2. Execute the generated Cypher script located at `cleaned/graph/neo4j_import.cypher` via `cypher-shell` or Neo4j Browser:",
        "```bash",
        "cypher-shell -u neo4j -p <password> -f cleaned/graph/neo4j_import.cypher",
        "```",
        "3. All constraints, transactional batches (5,000 rows/batch), and label mappings are pre-configured."
    ])

    with open(rep_dir / "graph_preparation_report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(rep_lines) + "\n")

    logger.info(f"Knowledge Graph data successfully prepared in {out_dir}")
    return summary


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Prepare Knowledge Graph data for Neo4j and NetworkX.")
    parser.add_argument("--data-path", default="cleaned/cleaned_patents_consolidated.parquet", help="Cleaned dataset path")
    parser.add_argument("--graph-dir", default="cleaned/graph", help="Graph output directory")
    parser.add_argument("--reports-dir", default="reports", help="Reports directory")
    parser.add_argument("--min-freq", type=int, default=5, help="Minimum concept frequency threshold")
    args = parser.parse_args()

    d_p = args.data_path
    g_d = args.graph_dir
    r_d = args.reports_dir
    if not os.path.exists(d_p) and os.path.exists(os.path.join("miniproject", d_p)):
        d_p = os.path.join("miniproject", d_p)
        g_d = os.path.join("miniproject", g_d)
        r_d = os.path.join("miniproject", r_d)

    summary = prepare_knowledge_graph(
        cleaned_data_path=d_p,
        graph_output_dir=g_d,
        reports_dir=r_d,
        min_concept_frequency=args.min_freq
    )
    print("\nKnowledge Graph preparation completed successfully!")
    print(f"Total Nodes: {summary['total_nodes']:,} | Total Edges: {summary['total_edges']:,}")
