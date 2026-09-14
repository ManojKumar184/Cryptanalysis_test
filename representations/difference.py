"""Replaceable, deterministic delta encoding for paired state trajectories."""

from __future__ import annotations

from dataclasses import dataclass

from core.sha_trace import SHA256dTrace


@dataclass(frozen=True)
class StateDifference:
    """XOR delta words indexed as ``[pass][block][round][word]``."""

    xor_words: tuple[tuple[tuple[tuple[int, ...], ...], ...], ...]

    @property
    def changed_word_count(self) -> int:
        return sum(word != 0 for pass_blocks in self.xor_words for block in pass_blocks for state in block for word in state)


def xor_difference(base: SHA256dTrace, modified: SHA256dTrace) -> StateDifference:
    def encode_pair(base_pass, modified_pass):
        if len(base_pass.compression_traces) != len(modified_pass.compression_traces):
            raise ValueError("trace block counts differ; trajectories are not alignable")
        return tuple(
            tuple(tuple(left ^ right for left, right in zip(base_state, modified_state)) for base_state, modified_state in zip(base_block.round_states, modified_block.round_states))
            for base_block, modified_block in zip(base_pass.compression_traces, modified_pass.compression_traces)
        )

    return StateDifference((encode_pair(base.first_pass, modified.first_pass), encode_pair(base.second_pass, modified.second_pass)))
