"""Ground-truth evaluation boundary; it performs no AI inference."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter_ns
from typing import Protocol

from .sha256d import sha256d, sha256d_with_trace
from .sha_trace import SHA256dTrace
from .target import Target


class ValidatedCandidate(Protocol):
    @property
    def is_validated(self) -> bool: ...

    def serialize(self) -> bytes: ...


@dataclass(frozen=True)
class EvaluationResult:
    digest: bytes
    success: bool
    sha256d_ns: int
    trace: SHA256dTrace | None = None


class Evaluator:
    def evaluate(self, candidate: ValidatedCandidate, target: Target, *, include_trace: bool = False) -> EvaluationResult:
        if not callable(getattr(candidate, "serialize", None)) or not getattr(candidate, "is_validated", False):
            raise TypeError("evaluation requires a validated candidate with serialize()")
        started = perf_counter_ns()
        traced = sha256d_with_trace(candidate.serialize()) if include_trace else None
        digest = traced.digest if traced else sha256d(candidate.serialize())
        elapsed = perf_counter_ns() - started
        return EvaluationResult(digest, target.accepts(digest), elapsed, traced.trace if traced else None)
