from pathlib import Path

from core.modifications import Modification
from learning.database import ExperienceDatabase
from learning.experience import Experience
from learning.model_manager import ModelManager
from learning.trainer import ContinualTrainer
from models.ranking_model import RankingModel


def test_committed_outcomes_train_and_version_the_ranking_model(tmp_path: Path) -> None:
    database = ExperienceDatabase(tmp_path / "archive.sqlite")
    for index, outcome in enumerate((False, True)):
        database.commit_experience(Experience.create(candidate_id="base", modified_candidate_id=f"m{index}", attempt_index=index, modification=Modification("nonce", index, index + 1), digest=bytes([index + 1]) * 32, target_hex="ff" * 32, success=outcome, feature_vector=(0.2 + index, 0.1)))
    ranking = RankingModel()
    result = ContinualTrainer().update(database, ModelManager(tmp_path / "models", database), ranking, batch_size=8)
    assert result.loss > 0
    assert result.model.path.exists()
    assert ranking.weights and ranking.probability((0.2, 0.1)) != 0.5
    database.close()
