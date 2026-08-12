from app.algorithms.team_assignment import assign_teams


def build_teams(student_ids: list[int], team_size: int = 5) -> list[list[int]]:
    return assign_teams(student_ids, team_size=team_size)

