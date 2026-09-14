"""Outcome-blind scoring interface for ordering legal modifications."""

from __future__ import annotations

from dataclasses import dataclass

from core.block import Candidate
from core.modifications import Modification


@dataclass(frozen=True)
class RankingModel:
    """A transparent initial scorer; trainer-owned weights arrive in Phase 4."""

    def score(self, candidate: Candidate, modification: Modification, mechanism_embedding: tuple[float, ...], state_features: tuple[float, ...], historical_signal: float = 0.0) -> float:
        if modification.before != candidate.mutable.as_dict()[modification.field]:
            raise ValueError("modification does not describe the supplied candidate")
        # The score intentionally excludes digest, target, and outcome data.
        change_scale = abs(modification.after - modification.before) / 0xFFFFFFFF
        structure = sum(mechanism_embedding) / max(1, len(mechanism_embedding))
        consequence = sum(state_features[:2])
        return change_scale + structure + consequence + historical_signal
