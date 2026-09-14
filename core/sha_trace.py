"""Immutable, candidate-specific SHA-256 execution trace schemas."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

WordState = tuple[int, int, int, int, int, int, int, int]


@dataclass(frozen=True)
class CompressionTrace:
    """Round states for one 512-bit SHA-256 compression block.

    ``round_states[i]`` is the eight-word working state after round ``i``;
    hence it contains exactly S0 through S63 for this compression pass.
    """

    block_index: int
    input_state: WordState
    round_states: tuple[WordState, ...]
    output_state: WordState

    def __post_init__(self) -> None:
        if len(self.round_states) != 64:
            raise ValueError("a SHA-256 compression trace must contain 64 round states")


@dataclass(frozen=True)
class SHA256Trace:
    """All compression traces needed for one SHA-256 digest."""

    compression_traces: tuple[CompressionTrace, ...]


@dataclass(frozen=True)
class SHA256dTrace:
    """Candidate-specific traces for the two explicit SHA-256d passes."""

    first_pass: SHA256Trace
    second_pass: SHA256Trace
