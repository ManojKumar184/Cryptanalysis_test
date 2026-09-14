import hashlib
import os

from core.sha256 import SHA256, sha256


def test_known_vectors() -> None:
    assert sha256(b"").hex() == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert sha256(b"abc").hex() == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_matches_hashlib_for_varied_lengths() -> None:
    for size in (0, 1, 55, 56, 63, 64, 65, 127, 128, 1024):
        payload = os.urandom(size)
        assert SHA256.digest(payload) == hashlib.sha256(payload).digest()


def test_trace_has_actual_64_round_states_per_block() -> None:
    _, trace = SHA256.digest_with_trace(b"a" * 64)
    assert len(trace.compression_traces) == 2
    assert all(len(item.round_states) == 64 for item in trace.compression_traces)
    assert trace.compression_traces[-1].output_state
