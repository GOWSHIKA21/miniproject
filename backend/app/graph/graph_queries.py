import os
import math
import pickle
import logging
from typing import Dict, Any, List, Optional
import networkx as nx
from backend.app.config import settings
from backend.app.database.neo4j_client import neo4j_client

logger = logging.getLogger(__name__)

COLOR_MAP = {
    "field": {"bg": "#e0e7ff", "text": "#4338ca", "border": "#c7d2fe"},
    "location": {"bg": "#dcfce7", "text": "#15803d", "border": "#bbf7d0"},
    "concept": {"bg": "#fef3c7", "text": "#b45309", "border": "#fde68a"},
    "app_type": {"bg": "#f3eefc", "text": "#6b46c1", "border": "#d8b4fe"},
    "patent": {"bg": "#6b46c1", "text": "white", "border": "#553c9a"}
}


class PatentGraphEngine:
    def __init__(self, graph_path: str = settings.GRAPH_STORE_PATH):
        self.graph_path = graph_path
        self.G: Optional[nx.MultiDiGraph] = None
        self._load_graph()

    def _load_graph(self):
        if os.path.exists(self.graph_path):
            try:
                with open(self.graph_path, "rb") as f:
                    self.G = pickle.load(f)
                logger.info(f"Loaded Knowledge Graph from {self.graph_path} with {self.G.number_of_nodes():,} nodes and {self.G.number_of_edges():,} edges")
            except Exception as e:
                logger.error(f"Error loading graph from {self.graph_path}: {e}")
                self.G = nx.MultiDiGraph()
        else:
            logger.warning(f"Graph file not found at {self.graph_path}. Initializing empty graph.")
            self.G = nx.MultiDiGraph()

    def _format_neo4j_subgraph(self, patent_id: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert Neo4j Cypher query results into React Flow graph structure."""
        nodes = []
        edges = []
        seen_nodes = set()
        seen_edges = set()

        first_rec = records[0]
        p_props = first_rec.get("p", {}) or {}
        p_title = p_props.get("title", patent_id)

        # Center: Target Patent Node
        nodes.append({
            "id": patent_id,
            "position": {"x": 350, "y": 220},
            "data": {
                "label": p_title[:50] + ("..." if len(p_title) > 50 else ""),
                "type": "patent",
                "metadata": p_props
            },
            "style": {
                "background": "#6b46c1",
                "color": "white",
                "borderRadius": "10px",
                "border": "2px solid #553c9a",
                "padding": "10px 14px",
                "fontWeight": "bold",
                "boxShadow": "0 4px 6px -1px rgba(0, 0, 0, 0.1)"
            }
        })
        seen_nodes.add(patent_id)

        # 1-hop targets
        targets = []
        for r in records:
            t = r.get("target")
            labels = r.get("target_labels", [])
            rel = r.get("rel", "connected to")
            if t and isinstance(t, dict):
                tid = t.get("id") or t.get("name") or str(t)
                t_label_type = "concept"
                for lbl in labels:
                    if lbl.lower() in ("field", "location", "concept", "applicationtype"):
                        t_label_type = "app_type" if lbl.lower() == "applicationtype" else lbl.lower()
                        break
                targets.append((tid, t, t_label_type, rel, r.get("p2")))

        num_neighbors = min(len(targets), 14)
        angle_step = (2 * math.pi) / max(num_neighbors, 1)
        radius = 220

        for idx, (tid, t_props, t_type, rel_name, p2) in enumerate(targets[:num_neighbors]):
            colors = COLOR_MAP.get(t_type, {"bg": "#f1f5f9", "text": "#334155", "border": "#cbd5e1"})
            x = 350 + int(radius * math.cos(idx * angle_step))
            y = 220 + int(radius * math.sin(idx * angle_step))

            if tid not in seen_nodes:
                label_val = t_props.get("name") or t_props.get("city") or tid
                nodes.append({
                    "id": str(tid),
                    "position": {"x": x, "y": y},
                    "data": {
                        "label": str(label_val),
                        "type": t_type,
                        "metadata": t_props
                    },
                    "style": {
                        "background": colors["bg"],
                        "color": colors["text"],
                        "border": f"1px solid {colors['border']}",
                        "borderRadius": "8px",
                        "padding": "8px 12px",
                        "fontSize": "12px",
                        "fontWeight": "500"
                    }
                })
                seen_nodes.add(tid)

            edge_id = f"e_{patent_id}_{tid}"
            if edge_id not in seen_edges:
                edges.append({
                    "id": edge_id,
                    "source": patent_id,
                    "target": str(tid),
                    "label": rel_name.replace("_", " ").lower(),
                    "animated": True,
                    "style": {"stroke": "#94a3b8", "strokeWidth": 1.5}
                })
                seen_edges.add(edge_id)

            # 2-hop connected patent
            if p2 and isinstance(p2, dict):
                p2_id = p2.get("id")
                if p2_id and p2_id not in seen_nodes and len(nodes) < 20:
                    p2_title = p2.get("title", p2_id)
                    nodes.append({
                        "id": str(p2_id),
                        "position": {"x": x + 150, "y": y + (idx % 2 * 60 - 30)},
                        "data": {
                            "label": f"Related: {p2_title[:35]}...",
                            "type": "patent",
                            "metadata": p2
                        },
                        "style": {
                            "background": "#f8fafc",
                            "color": "#475569",
                            "border": "1px dashed #94a3b8",
                            "borderRadius": "8px",
                            "padding": "6px 10px",
                            "fontSize": "11px"
                        }
                    })
                    seen_nodes.add(p2_id)
                    e2_id = f"e_{p2_id}_{tid}"
                    if e2_id not in seen_edges:
                        edges.append({
                            "id": e2_id,
                            "source": str(p2_id),
                            "target": str(tid),
                            "label": "also relates to",
                            "animated": False,
                            "style": {"stroke": "#cbd5e1", "strokeWidth": 1}
                        })
                        seen_edges.add(e2_id)

        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {"nodes": len(nodes), "edges": len(edges)}
        }

    def get_patent_subgraph(self, patent_id: str) -> Dict[str, Any]:
        """Generate React Flow compatible node and edge objects for a patent's 1-hop and 2-hop neighborhood."""
        # 1. Try Neo4j Aura if connected
        if neo4j_client.connected:
            try:
                cypher = """
                MATCH (p:Patent {id: $patent_id})-[r]->(target)
                OPTIONAL MATCH (target)<-[r2:RELATES_TO]-(p2:Patent) WHERE p2.id <> $patent_id
                RETURN p, type(r) AS rel, labels(target) AS target_labels, target, r2, p2
                LIMIT 16
                """
                records = neo4j_client.run_query(cypher, {"patent_id": patent_id})
                if records:
                    return self._format_neo4j_subgraph(patent_id, records)
            except Exception as e:
                logger.warning(f"Neo4j get_patent_subgraph query failed ({e}). Using NetworkX fallback.")

        # 2. Resilient Fallback: Local NetworkX Graph
        if not self.G or patent_id not in self.G:
            return {
                "nodes": [{
                    "id": patent_id or "1",
                    "position": {"x": 300, "y": 200},
                    "data": {"label": patent_id or "Patent Node", "type": "patent"},
                    "style": {"background": "#6b46c1", "color": "white", "borderRadius": "12px", "padding": "10px", "fontWeight": "bold"}
                }],
                "edges": [],
                "stats": {"nodes": 1, "edges": 0}
            }

        neighbors = list(self.G.neighbors(patent_id))
        nodes = []
        edges = []

        # Center: Target Patent Node
        p_data = self.G.nodes[patent_id]
        nodes.append({
            "id": patent_id,
            "position": {"x": 350, "y": 220},
            "data": {
                "label": p_data.get("full_title", patent_id)[:50] + "...",
                "type": "patent",
                "metadata": p_data
            },
            "style": {
                "background": "#6b46c1",
                "color": "white",
                "borderRadius": "10px",
                "border": "2px solid #553c9a",
                "padding": "10px 14px",
                "fontWeight": "bold",
                "boxShadow": "0 4px 6px -1px rgba(0, 0, 0, 0.1)"
            }
        })

        num_neighbors = min(len(neighbors), 14)
        angle_step = (2 * math.pi) / max(num_neighbors, 1)
        radius = 220

        second_hop_patents = set()

        for idx, n_id in enumerate(neighbors[:num_neighbors]):
            n_data = self.G.nodes[n_id]
            n_type = n_data.get("type", "concept")
            colors = COLOR_MAP.get(n_type, {"bg": "#f1f5f9", "text": "#334155", "border": "#cbd5e1"})
            
            x = 350 + int(radius * math.cos(idx * angle_step))
            y = 220 + int(radius * math.sin(idx * angle_step))

            nodes.append({
                "id": str(n_id),
                "position": {"x": x, "y": y},
                "data": {
                    "label": n_data.get("label", str(n_id)),
                    "type": n_type,
                    "metadata": n_data
                },
                "style": {
                    "background": colors["bg"],
                    "color": colors["text"],
                    "border": f"1px solid {colors['border']}",
                    "borderRadius": "8px",
                    "padding": "8px 12px",
                    "fontSize": "12px",
                    "fontWeight": "500"
                }
            })

            edges_data = self.G.get_edge_data(patent_id, n_id)
            edge_label = "connected to"
            if edges_data:
                first_edge_key = list(edges_data.keys())[0]
                edge_label = edges_data[first_edge_key].get("label", "connected to")

            edges.append({
                "id": f"e_{patent_id}_{n_id}",
                "source": patent_id,
                "target": str(n_id),
                "label": edge_label,
                "animated": True,
                "style": {"stroke": "#94a3b8", "strokeWidth": 1.5}
            })

            if n_type == "concept" and len(second_hop_patents) < 4:
                for predecessor, _, _ in self.G.in_edges(n_id, data=True):
                    if predecessor != patent_id and predecessor not in second_hop_patents:
                        second_hop_patents.add(predecessor)
                        pred_data = self.G.nodes.get(predecessor, {})
                        offset_x = x + 150
                        offset_y = y + (idx % 2 * 60 - 30)
                        nodes.append({
                            "id": str(predecessor),
                            "position": {"x": offset_x, "y": offset_y},
                            "data": {
                                "label": f"Related: {pred_data.get('full_title', predecessor)[:35]}...",
                                "type": "patent",
                                "metadata": pred_data
                            },
                            "style": {
                                "background": "#f8fafc",
                                "color": "#475569",
                                "border": "1px dashed #94a3b8",
                                "borderRadius": "8px",
                                "padding": "6px 10px",
                                "fontSize": "11px"
                            }
                        })
                        edges.append({
                            "id": f"e_{predecessor}_{n_id}",
                            "source": str(predecessor),
                            "target": str(n_id),
                            "label": "also relates to",
                            "animated": False,
                            "style": {"stroke": "#cbd5e1", "strokeWidth": 1}
                        })
                        break

        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {"nodes": len(nodes), "edges": len(edges)}
        }

    def get_related_patents(self, patent_id: str, limit: int = 8) -> List[Dict[str, Any]]:
        """Find related patents that share concepts or classifications."""
        # 1. Try Neo4j Aura if connected
        if neo4j_client.connected:
            try:
                cypher = """
                MATCH (p:Patent {id: $patent_id})-[:RELATES_TO]->(c:Concept)<-[:RELATES_TO]-(related:Patent)
                WHERE related.id <> $patent_id
                RETURN related.id AS patent_id, related.title AS title, related.field AS field, related.location AS location, count(c) AS shared_concepts_count
                ORDER BY shared_concepts_count DESC
                LIMIT $limit
                """
                records = neo4j_client.run_query(cypher, {"patent_id": patent_id, "limit": limit})
                if records:
                    return records
            except Exception as e:
                logger.warning(f"Neo4j get_related_patents query failed ({e}). Using NetworkX fallback.")

        # 2. Resilient Fallback: Local NetworkX Graph
        if not self.G or patent_id not in self.G:
            return []

        import re
        neighbors = list(self.G.neighbors(patent_id))
        concept_neighbors = [n for n in neighbors if self.G.nodes[n].get("type") == "concept"]

        candidate_scores = {}
        for c_id in concept_neighbors:
            for pred in self.G.predecessors(c_id):
                if pred != patent_id:
                    candidate_scores[pred] = candidate_scores.get(pred, 0) + 2

        if len(candidate_scores) < limit:
            field_neighbors = [n for n in neighbors if self.G.nodes[n].get("type") == "field"]
            target_title = self.G.nodes[patent_id].get("full_title", "").lower()
            target_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', target_title))

            for f_id in field_neighbors:
                for pred in list(self.G.predecessors(f_id))[:200]:
                    if pred != patent_id and pred not in candidate_scores:
                        pred_title = self.G.nodes.get(pred, {}).get("full_title", "").lower()
                        pred_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', pred_title))
                        overlap = len(target_words.intersection(pred_words))
                        candidate_scores[pred] = overlap + 1

        sorted_candidates = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        results = []
        for p_id, score in sorted_candidates:
            p_data = self.G.nodes.get(p_id, {})
            results.append({
                "patent_id": p_id,
                "title": p_data.get("full_title", p_id),
                "field": p_data.get("field", ""),
                "location": p_data.get("location", ""),
                "shared_concepts_count": score
            })
        return results

    def get_global_sample(self, max_patents: int = 10) -> Dict[str, Any]:
        """Sample a cohesive cluster of patents and entities for the global Graph Explorer view."""
        if not self.G or self.G.number_of_nodes() == 0:
            return {"nodes": [], "edges": [], "stats": {"nodes": 0, "edges": 0}}

        patent_nodes = [n for n, d in self.G.nodes(data=True) if d.get("type") == "patent"]
        if not patent_nodes:
            return {"nodes": [], "edges": [], "stats": {"nodes": 0, "edges": 0}}

        seed_patents = patent_nodes[:max_patents]
        relevant_nodes = set(seed_patents)
        for p in seed_patents:
            relevant_nodes.update(list(self.G.neighbors(p))[:4])

        subgraph = self.G.subgraph(relevant_nodes)
        
        nodes = []
        edges = []
        
        pos = nx.spring_layout(subgraph, k=0.5, iterations=30, seed=42)

        for n in subgraph.nodes():
            d = subgraph.nodes[n]
            n_type = d.get("type", "concept")
            colors = COLOR_MAP.get(n_type, {"bg": "#f1f5f9", "text": "#334155", "border": "#cbd5e1"})
            p = pos.get(n, [0, 0])
            
            label = d.get("label", str(n))
            if n_type == "patent":
                label = d.get("full_title", str(n))[:35] + "..."

            nodes.append({
                "id": str(n),
                "position": {"x": float(p[0] * 500 + 400), "y": float(p[1] * 400 + 250)},
                "data": {"label": label, "type": n_type, "metadata": d},
                "style": {
                    "background": colors["bg"],
                    "color": colors["text"],
                    "border": f"1px solid {colors['border']}",
                    "borderRadius": "8px",
                    "padding": "8px 12px",
                    "fontWeight": "600" if n_type == "patent" else "500",
                    "fontSize": "11px"
                }
            })

        for u, v, data in subgraph.edges(data=True):
            edges.append({
                "id": f"e_{u}_{v}",
                "source": str(u),
                "target": str(v),
                "label": data.get("label", ""),
                "animated": data.get("type") == "RELATES_TO",
                "style": {"stroke": "#94a3b8", "strokeWidth": 1.2}
            })

        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {"nodes": len(nodes), "edges": len(edges)}
        }


graph_engine = PatentGraphEngine()
