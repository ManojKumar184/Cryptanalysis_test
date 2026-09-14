"""Deterministic tensor-ready encoding of actual SHA-256d traces."""

from __future__ import annotations

from core.sha_trace import SHA256dTrace

_WORD_SCALE = float(0xFFFFFFFF)


def encode_trace(trace: SHA256dTrace) -> tuple[tuple[tuple[tuple[float, ...], ...], ...], ...]:
    """Return ``[pass][block][round][word]`` normalized to the closed unit interval."""
    return tuple(
        tuple(
            tuple(tuple(word / _WORD_SCALE for word in state) for state in block.round_states)
            for block in sha_trace.compression_traces
        )
        for sha_trace in (trace.first_pass, trace.second_pass)
    )
