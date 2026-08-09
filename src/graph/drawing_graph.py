"""NetworkX-backed graph representation of engineering drawing entities and topology."""
from __future__ import annotations

from typing import Any, Optional
import networkx as nx


class DrawingGraph:
    """Topology graph representation wrapper over NetworkX nx.Graph."""

    def __init__(self):
        self.graph = nx.Graph()

    def build(
        self,
        objects: list[Any],
        texts: list[Any],
        lines: list[Any],
        relationships: list[Any],
    ) -> nx.Graph:
        """Populate NetworkX graph with entity nodes and relationship edges.

        Parameters
        ----------
        objects : list
            List of DetectedObject dicts or Pydantic instances.
        texts : list
            List of ClassifiedText / ExtractedText dicts or Pydantic instances.
        lines : list
            List of DetectedLine dicts or Pydantic instances.
        relationships : list
            List of SpatialRelationship dicts or Pydantic instances.

        Returns
        -------
        nx.Graph
            Constructed NetworkX graph instance.
        """
        self.graph.clear()

        # Add Object nodes
        for obj in objects:
            obj_dict = obj.model_dump(mode="json") if hasattr(obj, "model_dump") else dict(obj)
            node_id = obj_dict.get("id")
            if node_id:
                self.graph.add_node(
                    node_id,
                    node_type="OBJECT",
                    category=obj_dict.get("type", "UNKNOWN"),
                    bbox=obj_dict.get("bbox"),
                    confidence=obj_dict.get("confidence", 1.0),
                    associated_text=obj_dict.get("associated_text"),
                )

        # Add Text nodes
        for txt in texts:
            txt_dict = txt.model_dump(mode="json") if hasattr(txt, "model_dump") else dict(txt)
            node_id = txt_dict.get("id")
            if node_id and node_id not in self.graph:
                self.graph.add_node(
                    node_id,
                    node_type="TEXT",
                    category=txt_dict.get("classification", "UNKNOWN"),
                    text=txt_dict.get("text", ""),
                    bbox=txt_dict.get("bbox"),
                    confidence=txt_dict.get("confidence", 1.0),
                )

        # Add Line nodes
        for line in lines:
            line_dict = line.model_dump(mode="json") if hasattr(line, "model_dump") else dict(line)
            node_id = line_dict.get("id")
            if node_id and node_id not in self.graph:
                self.graph.add_node(
                    node_id,
                    node_type="LINE",
                    category=line_dict.get("line_type", "UNKNOWN"),
                    orientation=line_dict.get("orientation"),
                    length=line_dict.get("length"),
                    confidence=line_dict.get("confidence", 1.0),
                )

        # Add Relationship edges
        for rel in relationships:
            rel_dict = rel.model_dump(mode="json") if hasattr(rel, "model_dump") else dict(rel)
            u = rel_dict.get("from_id")
            v = rel_dict.get("to_id")

            if u and v:
                # Ensure nodes exist if missing
                if u not in self.graph:
                    self.graph.add_node(u, node_type="UNKNOWN", category="UNKNOWN")
                if v not in self.graph:
                    self.graph.add_node(v, node_type="UNKNOWN", category="UNKNOWN")

                self.graph.add_edge(
                    u,
                    v,
                    relationship=rel_dict.get("relationship", "near"),
                    distance=rel_dict.get("distance", 0.0),
                    confidence=rel_dict.get("confidence", 1.0),
                )

        return self.graph

    def get_neighbors(self, node_id: str) -> list[str]:
        """Return list of neighbor node IDs connected to node_id."""
        if node_id not in self.graph:
            return []
        return list(self.graph.neighbors(node_id))

    def trace_from_object(self, start_node_id: str, max_depth: int = 5) -> list[str]:
        """Trace connectivity path starting from start_node_id using BFS traversal."""
        if start_node_id not in self.graph:
            return []

        visited = []
        queue = [(start_node_id, 0)]
        seen = {start_node_id}

        while queue:
            current, depth = queue.pop(0)
            visited.append(current)

            if depth < max_depth:
                for neighbor in self.graph.neighbors(current):
                    if neighbor not in seen:
                        seen.add(neighbor)
                        queue.append((neighbor, depth + 1))

        return visited

    def to_dict(self) -> dict:
        """Export graph to a serializable dictionary matching JSON schema standards."""
        nodes = []
        for n, attrs in self.graph.nodes(data=True):
            node_record = {"id": n}
            node_record.update(attrs)
            nodes.append(node_record)

        edges = []
        for u, v, attrs in self.graph.edges(data=True):
            edge_record = {"from_id": u, "to_id": v}
            edge_record.update(attrs)
            edges.append(edge_record)

        return {
            "num_nodes": self.graph.number_of_nodes(),
            "num_edges": self.graph.number_of_edges(),
            "nodes": nodes,
            "edges": edges,
        }
