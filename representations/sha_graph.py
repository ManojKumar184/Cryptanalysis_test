"""Static topology of SHA-256d, separate from candidate execution data."""

from __future__ import annotations

from dataclasses import dataclass

from core.sha256 import _K


@dataclass(frozen=True)
class GraphNode:
    node_id: str
    pass_index: int
    round_index: int
    constant: int
    kind: str = "round"


@dataclass(frozen=True)
class SHAGraph:
    nodes: tuple[GraphNode, ...]
    edges: tuple[tuple[str, str], ...]

    @classmethod
    def sha256d(cls) -> "SHAGraph":
        nodes = tuple(GraphNode(f"p{pass_id}:r{round_id}", pass_id, round_id, _K[round_id]) for pass_id in range(2) for round_id in range(64))
        edges: list[tuple[str, str]] = []
        for pass_id in range(2):
            for round_id in range(64):
                target = f"p{pass_id}:r{round_id}"
                if round_id:
                    edges.append((f"p{pass_id}:r{round_id - 1}", target))
                for dependency in (2, 7, 15, 16):
                    if round_id >= dependency:
                        edges.append((f"p{pass_id}:r{round_id - dependency}", target))
        # SHA-256d's second pass consumes the first digest after the final round.
        edges.append(("p0:r63", "p1:r0"))
        return cls(nodes, tuple(edges))
