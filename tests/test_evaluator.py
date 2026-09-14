import pytest

from core.block import Candidate, FixedFields, MutableFields
from core.evaluator import Evaluator
from core.target import Target


def test_evaluator_uses_exact_target_comparison_and_optional_trace() -> None:
    candidate = Candidate(FixedFields(b"p" * 32, b"m" * 32, 0x1D00FFFF), MutableFields(2, 1_700_000_000, 7))
    result = Evaluator().evaluate(candidate, Target((1 << 256) - 1), include_trace=True)
    assert result.success
    assert result.trace is not None
    assert result.sha256d_ns > 0


def test_target_rejects_digest_above_zero() -> None:
    assert not Target(0).accepts(bytes.fromhex("00" * 31 + "01"))


def test_evaluator_rejects_duck_typed_validation_claims() -> None:
    class ForgedCandidate:
        is_validated = True

        def serialize(self) -> bytes:
            return b"forged"

    with pytest.raises(TypeError):
        Evaluator().evaluate(ForgedCandidate(), Target(0))
