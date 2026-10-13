from fastapi import APIRouter
from typing import Dict, Any
from backend.app.schemas.graph import KnowledgeGraphResponse
from backend.app.graph.graph_queries import graph_engine

router = APIRouter(prefix="/graph", tags=["Knowledge Graph"])

@router.get("/sample")
def get_graph_sample():
    """Get cohesive cluster subgraph for interactive visualization in React Flow."""
    return graph_engine.get_global_sample(max_patents=8)

@router.get("/patent/{patent_id:path}")
def get_patent_graph(patent_id: str):
    """Get 1-hop and 2-hop neighborhood knowledge graph for a specific patent."""
    return graph_engine.get_patent_subgraph(patent_id)
