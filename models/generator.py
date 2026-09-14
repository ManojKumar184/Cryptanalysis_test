"""Deterministic proposal generation inside the formal legal mutation space."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from core.block import Candidate
from core.modifications import Modification


@dataclass(frozen=True)
class ModificationGenerator:
    """Initial proposal policy; not a sequential search or random baseline."""

    salt: str = "cryptoanalysis-v3"

    def propose(self, candidate: Candidate, proposal_index: int) -> Modification:
        if proposal_index < 0:
            raise ValueError("proposal index must be non-negative")
        fields = tuple(sorted(candidate.rules.enabled_mutable_fields))
        seed = sha256(f"{self.salt}:{candidate.candidate_id}:{proposal_index}".encode()).digest()
        field = fields[seed[0] % len(fields)]
        before = candidate.mutable.as_dict()[field]
        # Candidate-context-derived permutation avoids both sequential and random proposal baselines.
        after = int.from_bytes(seed[1:5], "big")
        if after == before:
            after = int.from_bytes(seed[5:9], "big") ^ 1
        return Modification.create(candidate, field, after)
