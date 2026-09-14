import hashlib

from core.sha256d import sha256d, sha256d_with_trace


def test_double_hash_matches_hashlib() -> None:
    data = b"Bitcoin-style candidate"
    assert sha256d(data) == hashlib.sha256(hashlib.sha256(data).digest()).digest()


def test_trace_explicitly_contains_both_passes() -> None:
    result = sha256d_with_trace(b"abc")
    assert len(result.trace.first_pass.compression_traces) == 1
    assert len(result.trace.second_pass.compression_traces) == 1
