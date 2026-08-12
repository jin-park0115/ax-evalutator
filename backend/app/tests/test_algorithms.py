from app.algorithms.seed_calculator import calculate_seed_scores
from app.algorithms.team_assignment import assign_teams


def test_assign_teams_by_team_size() -> None:
    assert assign_teams([1, 2, 3, 4, 5, 6], team_size=5) == [[1, 2, 3, 4, 5], [6]]


def test_calculate_seed_scores_average() -> None:
    assert calculate_seed_scores([{1: 80, 2: 70}, {1: 100}]) == {1: 90, 2: 70}

