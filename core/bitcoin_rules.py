"""The sole authority for permitted Bitcoin-style header mutations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


class BitcoinRuleViolation(ValueError):
    """A candidate or modification violates the experiment's legal space."""


@dataclass(frozen=True)
class BitcoinRules:
    """Validation for a deliberately narrow, serializable header experiment.

    The immutable portion contains the previous-block hash, merkle root, and
    compact target.  Version, timestamp, and nonce are enabled mutable header
    fields.  Each is consensus-serializable as an unsigned 32-bit word; this
    module is intentionally the only place that decides field legality.
    """

    enabled_mutable_fields: frozenset[str] = frozenset({"version", "timestamp", "nonce"})

    FIXED_FIELDS = frozenset({"previous_block_hash", "merkle_root", "bits"})
    MUTABLE_FIELDS = frozenset({"version", "timestamp", "nonce"})

    def validate_fixed(self, fields: Mapping[str, object]) -> None:
        if set(fields) != self.FIXED_FIELDS:
            raise BitcoinRuleViolation(f"fixed fields must be exactly {sorted(self.FIXED_FIELDS)}")
        for name in ("previous_block_hash", "merkle_root"):
            value = fields[name]
            if not isinstance(value, bytes) or len(value) != 32:
                raise BitcoinRuleViolation(f"{name} must be 32 raw bytes")
        self._validate_u32("bits", fields["bits"])

    def validate_mutable(self, fields: Mapping[str, object]) -> None:
        if not set(fields).issubset(self.enabled_mutable_fields):
            illegal = sorted(set(fields) - self.enabled_mutable_fields)
            raise BitcoinRuleViolation(f"disabled or unknown mutable fields: {illegal}")
        if set(fields) != self.enabled_mutable_fields:
            missing = sorted(self.enabled_mutable_fields - set(fields))
            raise BitcoinRuleViolation(f"missing enabled mutable fields: {missing}")
        for name, value in fields.items():
            self._validate_u32(name, value)

    def validate_change(self, field: str, before: object, after: object) -> None:
        if field not in self.enabled_mutable_fields:
            raise BitcoinRuleViolation(f"{field} is not enabled for mutation")
        self._validate_u32(field, before)
        self._validate_u32(field, after)
        if before == after:
            raise BitcoinRuleViolation("a modification must not be a no-op")

    @staticmethod
    def _validate_u32(name: str, value: object) -> None:
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 0xFFFFFFFF:
            raise BitcoinRuleViolation(f"{name} must be an unsigned 32-bit integer")
