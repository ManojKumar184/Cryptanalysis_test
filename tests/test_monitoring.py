from pathlib import Path

from learning.database import ExperienceDatabase
from monitoring.dashboard import snapshot
from monitoring.logger import EventLogger
from monitoring.metrics import MetricsStore
from worker import startup


def test_logging_metrics_and_dashboard_are_persistent_and_observational(tmp_path: Path) -> None:
    logger = EventLogger(tmp_path / "logs" / "events.jsonl")
    logger.log("EXPERIMENT_STARTED", {"source": "test"})
    database = ExperienceDatabase(tmp_path / "archive.sqlite")
    metrics = MetricsStore(database)
    metrics.record("wall_clock_ns", 3.0)
    assert metrics.latest()["wall_clock_ns"] == 3.0
    assert snapshot(database)["status"] == "OBSERVATIONAL"
    assert "EXPERIMENT_STARTED" in (tmp_path / "logs" / "events.jsonl").read_text()
    database.close()


def test_worker_startup_requires_and_uses_writable_persistent_root(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CRYPTOANALYSIS_DATA_ROOT", str(tmp_path / "persistent"))
    database, checkpoints, logger = startup()
    assert database.path.exists()
    assert checkpoints.root.exists()
    assert logger.path.exists()
    database.close()
