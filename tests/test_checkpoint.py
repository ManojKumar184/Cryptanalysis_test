from pathlib import Path

from persistence.checkpoint import CheckpointManager
from persistence.recovery import RecoveryManager


def state(index: int) -> dict[str, object]:
    return {"controller_state": "PAUSED", "candidate": {"id": index}, "attempt_index": index, "model_version": None, "experience_count": index, "configuration_version": "v3"}


def test_atomic_checkpoint_round_trip_and_corruption_fallback(tmp_path: Path) -> None:
    manager = CheckpointManager(tmp_path)
    first = manager.create(state(1))
    second = manager.create(state(2))
    second.write_text("corrupt", encoding="utf-8")
    recovered = RecoveryManager().recover(manager)
    assert recovered.checkpoint_path == first
    assert recovered.state and recovered.state["attempt_index"] == 1
