from pathlib import Path

import pytest

from core.target import Target
from core.modifications import DuplicateCandidateError
from experiment.controller import ExperimentController
from learning.database import ExperienceDatabase
from persistence.checkpoint import CheckpointManager
from persistence.recovery import RecoveryManager
from tests.test_block import make_candidate


def test_restart_restores_candidate_attempt_and_duplicate_guard(tmp_path: Path) -> None:
    database = ExperienceDatabase(tmp_path / "archive.sqlite")
    checkpoints = CheckpointManager(tmp_path / "checkpoints")
    original = ExperimentController(database, checkpoints, Target(0))
    original.set_candidate(make_candidate())
    original.run_one_attempt()
    recovered = RecoveryManager().recover(checkpoints)
    resumed = ExperimentController(database, checkpoints, Target(0))
    resumed.restore(recovered.state)
    assert resumed.current_candidate == original.current_candidate
    assert resumed.attempt_index == original.attempt_index
    # A fresh engine must still avoid the already committed modified candidate.
    with pytest.raises(DuplicateCandidateError):
        resumed.search.validator.apply(resumed.current_candidate, resumed.search.generator.propose(resumed.current_candidate, 0))
