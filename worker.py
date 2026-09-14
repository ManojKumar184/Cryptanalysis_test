"""Restart-safe worker entry point. Autonomous operation requires an explicit integrity gate."""

from __future__ import annotations

import os
import signal
from pathlib import Path

from learning.database import ExperienceDatabase
from monitoring.logger import EventLogger
from persistence.checkpoint import CheckpointManager
from persistence.recovery import RecoveryManager


def persistent_root() -> Path:
    return Path(os.environ.get("CRYPTOANALYSIS_DATA_ROOT", "/data/cryptoanalysis"))


def startup() -> tuple[ExperienceDatabase, CheckpointManager, EventLogger]:
    root = persistent_root()
    root.mkdir(parents=True, exist_ok=True)
    probe = root / ".write_probe"
    probe.write_text("ok", encoding="utf-8")
    probe.unlink()
    database = ExperienceDatabase(root / "database" / "cryptoanalysis.sqlite")
    checkpoints = CheckpointManager(root / "checkpoints")
    logger = EventLogger(root / "logs" / "events.jsonl")
    recovery = RecoveryManager().recover(checkpoints)
    logger.log("EXPERIMENT_RESUMED" if recovery.state else "EXPERIMENT_STARTED", {"checkpoint": str(recovery.checkpoint_path) if recovery.checkpoint_path else None})
    return database, checkpoints, logger


def main() -> None:
    database, _, logger = startup()
    integrity_gate = os.environ.get("CRYPTOANALYSIS_INTEGRITY_VERIFIED") == "1"
    autonomous_requested = os.environ.get("CRYPTOANALYSIS_AUTONOMOUS") == "1"
    if autonomous_requested and not integrity_gate:
        logger.log("ERROR", {"reason": "autonomous mode refused: integrity gate not verified"})
        raise SystemExit("autonomous mode requires CRYPTOANALYSIS_INTEGRITY_VERIFIED=1")
    logger.log("PAUSED", {"reason": "autonomous mode disabled" if not autonomous_requested else "controller scheduling not configured"})
    database.close()


if __name__ == "__main__":
    main()
