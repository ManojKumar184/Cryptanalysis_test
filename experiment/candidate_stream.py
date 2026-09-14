"""Durably creates the next Bitcoin-style candidate context."""

from __future__ import annotations

import json
import os
from hashlib import sha256
from pathlib import Path

from core.block import Candidate, FixedFields, MutableFields


class CandidateStream:
    def __init__(self, state_path: str | Path) -> None:
        self.state_path = Path(state_path)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.sequence = int(json.loads(self.state_path.read_text())["sequence"]) if self.state_path.exists() else 0

    def next(self, predecessor: Candidate | None = None) -> Candidate:
        context = predecessor.serialize() if predecessor else b"cryptoanalysis-v3-genesis"
        seed = sha256(context + self.sequence.to_bytes(8, "big")).digest()
        candidate = Candidate(FixedFields(seed, sha256(seed).digest(), 0x1D00FFFF), MutableFields(2, 1_700_000_000 + self.sequence, int.from_bytes(seed[:4], "little")), {"stream_sequence": str(self.sequence)})
        self.sequence += 1
        temporary = self.state_path.with_suffix(".tmp")
        temporary.write_text(json.dumps({"sequence": self.sequence}), encoding="utf-8")
        os.replace(temporary, self.state_path)
        return candidate
