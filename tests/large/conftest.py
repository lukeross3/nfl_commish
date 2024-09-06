import pytest

from nfl_commish.team_classifier import TeamClassifier


@pytest.fixture(scope="session")
def classifier() -> TeamClassifier:
    return TeamClassifier()
