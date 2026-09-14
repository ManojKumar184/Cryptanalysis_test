from dataclasses import dataclass

from core.evaluator import Evaluator
from core.target import Target


@dataclass
class Candidate:
    data: bytes

    def serialize(self) -> bytes:
        return self.data


def test_evaluator_uses_exact_target_comparison_and_optional_trace() -> None:
    result = Evaluator().evaluate(Candidate(b"abc"), Target((1 << 256) - 1), include_trace=True)
    assert result.success
    assert result.trace is not None
    assert result.sha256d_ns > 0


def test_target_rejects_digest_above_zero() -> None:
    assert not Target(0).accepts(bytes.fromhex("00" * 31 + "01"))
