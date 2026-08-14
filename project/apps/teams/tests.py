from apps.teams.services import assign_teams


def test_assign_teams_by_team_size() -> None:
    assert assign_teams([1, 2, 3, 4, 5, 6], team_size=5) == [[1, 2, 3, 4, 5], [6]]
