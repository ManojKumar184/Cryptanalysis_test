"""Explicit C(F,M) Bitcoin-style candidate representation."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Mapping

from .bitcoin_rules import BitcoinRules


@dataclass(frozen=True)
class FixedFields:
    previous_block_hash: bytes
    merkle_root: bytes
    bits: int

    def as_dict(self) -> dict[str, object]:
        return {"previous_block_hash": self.previous_block_hash, "merkle_root": self.merkle_root, "bits": self.bits}


@dataclass(frozen=True)
class MutableFields:
    version: int
    timestamp: int
    nonce: int

    def as_dict(self) -> dict[str, int]:
        return {"version": self.version, "timestamp": self.timestamp, "nonce": self.nonce}

    def replace(self, field_name: str, value: int) -> "MutableFields":
        if field_name not in self.as_dict():
            raise KeyError(field_name)
        return MutableFields(**(self.as_dict() | {field_name: value}))


@dataclass(frozen=True)
class Candidate:
    """Validated candidate ``C(F,M)`` with deterministic 80-byte serialization."""

    fixed: FixedFields
    mutable: MutableFields
    metadata: Mapping[str, str] = field(default_factory=dict, compare=False, hash=False, repr=False)
    rules: BitcoinRules = field(default_factory=BitcoinRules, compare=False, hash=False, repr=False)

    def __post_init__(self) -> None:
        self.rules.validate_fixed(self.fixed.as_dict())
        self.rules.validate_mutable(self.mutable.as_dict())
        if not all(isinstance(key, str) and isinstance(value, str) for key, value in self.metadata.items()):
            raise ValueError("candidate metadata must be string-to-string")

    @property
    def candidate_id(self) -> str:
        """Stable ID based solely on the canonical serialized candidate."""
        return sha256(self.serialize()).hexdigest()

    @property
    def is_validated(self) -> bool:
        return True

    def serialize(self) -> bytes:
        """Bitcoin header wire order: words little-endian, hash fields raw wire bytes."""
        return b"".join((
            self.mutable.version.to_bytes(4, "little"),
            self.fixed.previous_block_hash,
            self.fixed.merkle_root,
            self.mutable.timestamp.to_bytes(4, "little"),
            self.fixed.bits.to_bytes(4, "little"),
            self.mutable.nonce.to_bytes(4, "little"),
        ))

    def with_mutable(self, field_name: str, value: int) -> "Candidate":
        return Candidate(self.fixed, self.mutable.replace(field_name, value), dict(self.metadata), self.rules)
