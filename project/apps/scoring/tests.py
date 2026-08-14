from apps.scoring.services import calculate_seed_scores


def test_calculate_seed_scores_average() -> None:
    assert calculate_seed_scores([{1: 80, 2: 70}, {1: 100}]) == {1: 90, 2: 70}
