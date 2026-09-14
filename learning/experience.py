"""Canonical durable record produced only after exact evaluation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Mapping

from core.modifications import Modification


@dataclass(frozen=True)
class Experience:
    candidate_id: str
    modified_candidate_id: str
    attempt_index: int
    modification: Modification
    model_version: str | None
    score: float | None
    digest: bytes
    target_hex: str
    success: bool
    trace_reference: str | None
    difference_reference: str | None
    timings_ns: Mapping[str, int]
    timestamp: str

    @classmethod
    def create(cls, *, candidate_id: str, modified_candidate_id: str, attempt_index: int, modification: Modification, digest: bytes, target_hex: str, success: bool, model_version: str | None = None, score: float | None = None, trace_reference: str | None = None, difference_reference: str | None = None, timings_ns: Mapping[str, int] | None = None) -> "Experience":
        if attempt_index < 0:
            raise ValueError("attempt index must be non-negative")
        if len(digest) != 32:
            raise ValueError("experience digest must be 32 bytes")
        return cls(candidate_id, modified_candidate_id, attempt_index, modification, model_version, score, digest, target_hex, success, trace_reference, difference_reference, dict(timings_ns or {}), datetime.now(timezone.utc).isoformat())

    def to_row(self) -> dict[str, object]:
        row = asdict(self)
        row["digest"] = self.digest.hex()
        row["modification"] = asdict(self.modification)
        return row
