import pytest

from core.bitcoin_rules import BitcoinRuleViolation
from core.block import Candidate, FixedFields, MutableFields


def make_candidate() -> Candidate:
    return Candidate(FixedFields(b"p" * 32, b"m" * 32, 0x1D00FFFF), MutableFields(2, 1_700_000_000, 7))


def test_candidate_is_explicit_fixed_mutable_and_serializes_header() -> None:
    candidate = make_candidate()
    assert len(candidate.serialize()) == 80
    assert candidate.serialize()[:4] == b"\x02\x00\x00\x00"
    assert candidate.candidate_id == make_candidate().candidate_id


def test_invalid_fixed_or_mutable_fields_are_rejected() -> None:
    with pytest.raises(BitcoinRuleViolation):
        Candidate(FixedFields(b"x", b"m" * 32, 1), MutableFields(1, 2, 3))
    with pytest.raises(BitcoinRuleViolation):
        Candidate(FixedFields(b"p" * 32, b"m" * 32, 1), MutableFields(1, 2, -1))
