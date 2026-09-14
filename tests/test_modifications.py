import pytest

from core.bitcoin_rules import BitcoinRuleViolation
from core.modifications import DuplicateCandidateError, Modification, ModificationValidator
from tests.test_block import make_candidate


def test_legal_modification_records_before_after_and_changes_candidate() -> None:
    base = make_candidate()
    modification = Modification.create(base, "nonce", 8)
    result = ModificationValidator().apply(base, modification)
    assert modification.before == 7
    assert modification.after == 8
    assert modification.changed_fields == ("nonce",)
    assert result.mutable.nonce == 8
    assert result.serialize() != base.serialize()


def test_illegal_noop_and_duplicate_modifications_are_rejected() -> None:
    base = make_candidate()
    with pytest.raises(BitcoinRuleViolation):
        Modification.create(base, "bits", 1)
    with pytest.raises(BitcoinRuleViolation):
        Modification.create(base, "nonce", 7)
    validator = ModificationValidator()
    modification = Modification.create(base, "nonce", 8)
    validator.apply(base, modification)
    with pytest.raises(DuplicateCandidateError):
        validator.apply(base, modification)
