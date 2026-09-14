"""First-class legal modification validation and duplicate detection."""

from __future__ import annotations

from dataclasses import dataclass

from .bitcoin_rules import BitcoinRules
from .block import Candidate


class DuplicateCandidateError(ValueError):
    """A mutation resulted in a candidate already observed in this scope."""


@dataclass(frozen=True)
class Modification:
    field: str
    before: int
    after: int

    @classmethod
    def create(cls, candidate: Candidate, field: str, after: int) -> "Modification":
        before = candidate.mutable.as_dict().get(field)
        if before is None:
            candidate.rules.validate_change(field, after, after)
        candidate.rules.validate_change(field, before, after)
        return cls(field, before, after)

    def apply(self, candidate: Candidate) -> Candidate:
        candidate.rules.validate_change(self.field, candidate.mutable.as_dict().get(self.field), self.after)
        if candidate.mutable.as_dict()[self.field] != self.before:
            raise ValueError("modification before value does not match candidate")
        return candidate.with_mutable(self.field, self.after)

    @property
    def changed_fields(self) -> tuple[str, ...]:
        return (self.field,)


class ModificationValidator:
    """Validates and applies mutations while tracking canonical result IDs."""

    def __init__(self, rules: BitcoinRules | None = None) -> None:
        self.rules = rules or BitcoinRules()
        self._seen_candidate_ids: set[str] = set()

    def register(self, candidate: Candidate) -> None:
        self._seen_candidate_ids.add(candidate.candidate_id)

    def register_id(self, candidate_id: str) -> None:
        """Preload a durably committed candidate identity during recovery."""
        self._seen_candidate_ids.add(candidate_id)

    def apply(self, candidate: Candidate, modification: Modification) -> Candidate:
        if candidate.rules != self.rules:
            raise ValueError("candidate rules do not match modification validator rules")
        result = modification.apply(candidate)
        if result.candidate_id in self._seen_candidate_ids:
            raise DuplicateCandidateError(f"duplicate candidate {result.candidate_id}")
        self._seen_candidate_ids.add(result.candidate_id)
        return result
