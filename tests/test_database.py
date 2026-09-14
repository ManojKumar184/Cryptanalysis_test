from pathlib import Path

import pytest

from core.modifications import Modification
from learning.database import DuplicateExperienceError, ExperienceDatabase
from learning.experience import Experience
from learning.replay import ReplaySampler


def experience(index: int, success: bool = False) -> Experience:
    return Experience.create(candidate_id="base", modified_candidate_id=f"modified-{index}", attempt_index=index, modification=Modification("nonce", index, index + 1), digest=bytes([index + 1]) * 32, target_hex="ff" * 32, success=success)


def test_commit_is_transactional_and_prevents_duplicate_attempts(tmp_path: Path) -> None:
    database = ExperienceDatabase(tmp_path / "archive.sqlite")
    assert database.commit_experience(experience(0)) == 1
    assert database.count_experiences() == 1
    with pytest.raises(DuplicateExperienceError):
        database.commit_experience(experience(0))
    assert database.count_experiences() == 1
    database.close()


def test_replay_uses_complete_archive_with_mixed_recent_records(tmp_path: Path) -> None:
    database = ExperienceDatabase(tmp_path / "archive.sqlite")
    for index in range(6):
        database.commit_experience(experience(index, success=index == 2))
    sample = ReplaySampler().sample(database, 4)
    assert len(sample) == 4
    assert any(row["success"] for row in sample)
    assert any(row["attempt_index"] == 5 for row in sample)
    database.close()
