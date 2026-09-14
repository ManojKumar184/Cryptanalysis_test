"""A dependency-free structural encoder for the fixed SHA-256d graph."""

from __future__ import annotations

from dataclasses import dataclass

from representations.sha_graph import SHAGraph


@dataclass(frozen=True)
class SHA256dGNN:
    """Topology embedding used as a stable mechanism feature, not a predictor."""

    embedding_size: int = 8

    def forward(self, graph: SHAGraph) -> tuple[float, ...]:
        if not graph.nodes:
            raise ValueError("graph must contain nodes")
        indegrees = {node.node_id: 0 for node in graph.nodes}
        for _, target in graph.edges:
            indegrees[target] += 1
        constant_mean = sum(node.constant / 0xFFFFFFFF for node in graph.nodes) / len(graph.nodes)
        return (
            len(graph.nodes) / 128.0,
            len(graph.edges) / 1024.0,
            sum(node.pass_index for node in graph.nodes) / len(graph.nodes),
            sum(node.round_index for node in graph.nodes) / (len(graph.nodes) * 63),
            constant_mean,
            min(indegrees.values()) / 8.0,
            max(indegrees.values()) / 8.0,
            sum(indegrees.values()) / (len(graph.nodes) * 8),
        )[: self.embedding_size]
