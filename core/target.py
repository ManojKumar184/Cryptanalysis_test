"""Canonical target comparison, independent of all model outputs."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Target:
    value: int

    def __post_init__(self) -> None:
        if not 0 <= self.value < 1 << 256:
            raise ValueError("target must be an unsigned 256-bit integer")

    @classmethod
    def from_hex(cls, value: str) -> "Target":
        value = value.removeprefix("0x")
        if not value or len(value) > 64:
            raise ValueError("target hex must contain 1 to 64 digits")
        return cls(int(value, 16))

    def accepts(self, digest: bytes) -> bool:
        if len(digest) != 32:
            raise ValueError("digest must be exactly 32 bytes")
        return int.from_bytes(digest, "big") <= self.value

    def to_hex(self) -> str:
        return f"{self.value:064x}"
