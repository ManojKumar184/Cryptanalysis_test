"""Feature extraction from actual base/modified internal state traces."""

from __future__ import annotations

from dataclasses import dataclass

from representations.difference import StateDifference
from representations.state_encoder import encode_trace
from core.sha_trace import SHA256dTrace


@dataclass(frozen=True)
class DifferenceModel:
    """Produces diagnostics only; it has no target or success/failure input."""

    def forward(self, base: SHA256dTrace, modified: SHA256dTrace, difference: StateDifference, mechanism_embedding: tuple[float, ...]) -> tuple[float, ...]:
        base_encoding = encode_trace(base)
        modified_encoding = encode_trace(modified)
        base_words = [word for pass_blocks in base_encoding for block in pass_blocks for state in block for word in state]
        modified_words = [word for pass_blocks in modified_encoding for block in pass_blocks for state in block for word in state]
        if len(base_words) != len(modified_words):
            raise ValueError("encoded trajectories must have equal shape")
        absolute_shift = sum(abs(left - right) for left, right in zip(base_words, modified_words)) / len(base_words)
        changed_fraction = difference.changed_word_count / len(base_words)
        return (absolute_shift, changed_fraction, *mechanism_embedding)
