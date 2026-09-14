from pathlib import Path

from core.target import Target
from experiment.controller import ControllerState, ExperimentController
from learning.database import ExperienceDatabase
from persistence.checkpoint import CheckpointManager
from tests.test_block import make_candidate


def test_controller_records_exact_failure_and_checkpoints(tmp_path: Path) -> None:
    controller = ExperimentController(ExperienceDatabase(tmp_path / "database.sqlite"), CheckpointManager(tmp_path / "checkpoints"), Target(0))
    controller.set_candidate(make_candidate())
    assert not controller.run_one_attempt()
    assert controller.database.count_experiences() == 1
    assert controller.state == ControllerState.CHECKPOINTING
    assert controller.checkpoints.valid_checkpoints_newest_first()
