from pathlib import Path

from learning.database import ExperienceDatabase
from learning.model_manager import ModelManager


def test_model_versions_are_immutable_and_auditable(tmp_path: Path) -> None:
    database = ExperienceDatabase(tmp_path / "archive.sqlite")
    manager = ModelManager(tmp_path / "models", database)
    first = manager.create_version({"weight": 1}, experience_count=0, metrics={"x": 1.0}, promote=True)
    second = manager.create_version({"weight": 2}, experience_count=2, metrics={"x": 2.0}, promote=False)
    assert first.version == "model_000001"
    assert second.parent_version == first.version
    assert first.path.exists() and second.path.exists()
    database.close()
