"""Recovery selects the newest integrity-valid checkpoint, with fallback."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .checkpoint import CheckpointManager


@dataclass(frozen=True)
class RecoveryResult:
    checkpoint_path: Path | None
    state: dict[str, object] | None


class RecoveryManager:
    def recover(self, checkpoints: CheckpointManager) -> RecoveryResult:
        valid = checkpoints.valid_checkpoints_newest_first()
        return RecoveryResult(*valid[0]) if valid else RecoveryResult(None, None)
