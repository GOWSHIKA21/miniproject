from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class GraphNodeData(BaseModel):
    label: str
    type: str  # 'patent', 'field', 'location', 'concept', 'app_type'
    metadata: Optional[Dict[str, Any]] = None

class GraphNode(BaseModel):
    id: str
    position: Dict[str, float]
    data: GraphNodeData
    style: Optional[Dict[str, Any]] = None
    type: Optional[str] = "default"

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str] = None
    animated: Optional[bool] = False
    style: Optional[Dict[str, Any]] = None

class KnowledgeGraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    stats: Dict[str, int]
