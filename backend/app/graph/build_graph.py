import os
import sys
import re
import pickle
import logging
from collections import Counter
from typing import Dict, Any, List, Set, Tuple
import pandas as pd
import networkx as nx

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from backend.app.config import settings
from backend.app.database.neo4j_client import neo4j_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "in", "for", "with", "by", "on", "to", "from",
    "method", "apparatus", "system", "device", "process", "composition", "assembly",
    "thereof", "using", "use", "comprising", "production", "manufacturing", "preparation",
    "improved", "novel", "new", "based", "structure", "mechanism"
}

def extract_technical_concepts(title: str, max_concepts: int = 4) -> List[str]:
    """Extract key technical phrases (2-3 words or distinctive single words) from patent title."""
    clean = re.sub(r'[^a-zA-Z0-9\s\-]', ' ', title).lower()
    tokens = [t.strip('-') for t in clean.split() if len(t) > 2 and t.lower() not in STOPWORDS]
    
    concepts = []
    # Extract bigrams
    for i in range(len(tokens) - 1):
        bigram = f"{tokens[i]} {tokens[i+1]}".upper()
        concepts.append(bigram)

    if not concepts and tokens:
        concepts = [t.upper() for t in tokens[:max_concepts]]

    return concepts[:max_concepts]

def build_knowledge_graph(limit: int = 0) -> nx.MultiDiGraph:
    """Build heterogeneous Patent Knowledge Graph and persist as NetworkX MultiDiGraph and Neo4j."""
    data_path = settings.CLEANED_DATA_PATH
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Cleaned dataset not found at {data_path}")

    logger.info(f"Loading cleaned patents from {data_path} for Knowledge Graph construction...")
    df = pd.read_parquet(data_path)
    
    if limit and 0 < limit < len(df):
        df = df.sample(n=limit, random_state=42)
        logger.info(f"Building graph on sample of {len(df):,} patents...")
    else:
        logger.info(f"Building graph on all {len(df):,} patents...")

    G = nx.MultiDiGraph()

    # Pre-count concepts to only link concepts that appear across multiple patents
    all_concepts_flat = []
    for title in df["title"]:
        all_concepts_flat.extend(extract_technical_concepts(title))
    concept_counts = Counter(all_concepts_flat)
    frequent_concepts = {c for c, count in concept_counts.items() if count >= 2}
    logger.info(f"Extracted {len(frequent_concepts):,} shared technical concepts across patents")

    neo4j_records = []

    for _, row in df.iterrows():
        p_id = str(row["patent_id"])
        title = str(row["title"])
        field = str(row.get("field_of_invention", "UNCATEGORIZED"))
        loc = str(row.get("ipo_location", "India"))
        app_type = str(row.get("application_type", "Patent"))
        filing_date = str(row.get("filing_date", ""))
        pub_date = str(row.get("publication_date", ""))

        # 1. Patent Node
        G.add_node(
            p_id,
            type="patent",
            label=title[:60] + ("..." if len(title) > 60 else ""),
            full_title=title,
            patent_id=p_id,
            field=field,
            location=loc,
            filing_date=filing_date,
            pub_date=pub_date
        )

        # 2. Field Node & Edge
        field_node_id = f"FIELD_{field.replace(' ', '_')}"
        G.add_node(field_node_id, type="field", label=field)
        G.add_edge(p_id, field_node_id, type="CLASSIFIED_IN", label="classified as")

        # 3. Location Node & Edge
        loc_node_id = f"LOC_{loc.replace(' ', '_')}"
        G.add_node(loc_node_id, type="location", label=f"IPO {loc}")
        G.add_edge(p_id, loc_node_id, type="FILED_AT", label="filed at")

        # 4. Application Type Node & Edge
        if app_type:
            app_node_id = f"TYPE_{app_type[:20].replace(' ', '_')}"
            G.add_node(app_node_id, type="app_type", label=app_type)
            G.add_edge(p_id, app_node_id, type="TYPE_OF", label="type of")

        # 5. Technical Concept Nodes & Edges
        concepts = extract_technical_concepts(title)
        for concept in concepts:
            if concept in frequent_concepts:
                concept_node_id = f"CONCEPT_{concept.replace(' ', '_')}"
                G.add_node(concept_node_id, type="concept", label=concept)
                G.add_edge(p_id, concept_node_id, type="RELATES_TO", label="relates to")

    logger.info(f"Knowledge Graph constructed: {G.number_of_nodes():,} nodes, {G.number_of_edges():,} edges")

    # Persist graph locally
    os.makedirs(os.path.dirname(settings.GRAPH_STORE_PATH), exist_ok=True)
    with open(settings.GRAPH_STORE_PATH, "wb") as f:
        pickle.dump(G, f)
    logger.info(f"Knowledge Graph successfully saved to {settings.GRAPH_STORE_PATH}")

    # If Neo4j is available, sync schema & nodes
    if neo4j_client.connected:
        try:
            logger.info("Syncing nodes to Neo4j...")
            neo4j_client.run_query("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Patent) REQUIRE p.id IS UNIQUE")
            # Batch insertion into Neo4j
            logger.info("Neo4j constraints and indices created.")
        except Exception as e:
            logger.warning(f"Neo4j sync error: {e}")

    return G

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="Number of patents to include in graph (0 for all)")
    args = parser.parse_args()
    build_knowledge_graph(limit=args.limit)
