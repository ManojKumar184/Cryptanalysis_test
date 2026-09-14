"""Exact double-SHA-256 with traces for both constituent passes."""

from __future__ import annotations

from dataclasses import dataclass

from .sha256 import SHA256
from .sha_trace import SHA256dTrace


@dataclass(frozen=True)
class SHA256dResult:
    digest: bytes
    trace: SHA256dTrace


def sha256d(message: bytes) -> bytes:
    return SHA256.digest(SHA256.digest(message))


def sha256d_with_trace(message: bytes) -> SHA256dResult:
    first_digest, first_trace = SHA256.digest_with_trace(message)
    digest, second_trace = SHA256.digest_with_trace(first_digest)
    return SHA256dResult(digest=digest, trace=SHA256dTrace(first_trace, second_trace))
